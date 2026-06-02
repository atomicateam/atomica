"""
Implements the parameter function parser

Parameter functions are entered as strings in the Framework file.
This module implements the function parser that converts the string into
an executable Python representation.

"""

import ast
import numpy as np
from functools import reduce, cache

__all__ = ["parse_function"]


def sdiv(numerator, denominator):
    """
    Safe division by zero (return 0)

    This helper function returns division where ``0/0=0`` rather than ``np.nan``.

    :param numerator: The numerator of the operation (float, array)
    :param denominator: The denominator of the operation (float, array)
    :return: Array
    """

    if np.isscalar(numerator):
        if np.isscalar(denominator):
            # If both arguments are scalars, avoid creating any numpy arrays
            if numerator == 0:
                return 0.0
            elif denominator == 0:
                # If the denominator is 0, going via np.divide will return np.inf *and* display the expected RuntimeWarning
                return np.divide(numerator, denominator)
            else:
                return numerator / denominator
        else:
            # Return the output using np.divide, sized by the denominator
            return np.divide(numerator, denominator, out=np.zeros_like(denominator, dtype=float), where=numerator != 0)
    else:
        # Return the output using np.divide, sized by the numerator
        return np.divide(numerator, denominator, out=np.zeros_like(numerator, dtype=float), where=numerator != 0)


def vector_min(*args):
    """
    Repeated elementwise minimum

    Repeatedly call `np.minimum` so that both scalars and arrays are supported
    as well as >2 items.

    All arrays provided (if any) must be the same size

    Example:

        >>> vector_min([1,2],0,[-1,1])
        array([-1,  0])

    :param args: Scalars or arrays to take minimum over
    :return: Result of calling `np.minimum` repeatedly
        - Scalar if all inputs are scalar
        - np.array if any input is an array
    """
    return reduce(np.minimum, args)


def vector_max(*args):
    """
    Repeated elementwise maximum

    Repeatedly call `np.maximum` so that both scalars and arrays are supported
    as well as >2 items.

    All arrays provided (if any) must be the same size

    Example:

        >>> vector_max([1,2],5,[10,1])
        array([10,  5])

    :param args: Scalars or arrays to take maximum over
    :return: Result of calling `np.maximum` repeatedly
        - Scalar if all inputs are scalar
        - np.array if any input is an array
    """
    return reduce(np.maximum, args)


# Only calls to functions in the dict below will be permitted
supported_functions = {"max": vector_max, "min": vector_min, "exp": np.exp, "floor": np.floor, "SRC_POP_AVG": None, "TGT_POP_AVG": None, "SRC_POP_SUM": None, "TGT_POP_SUM": None, "STITCH_AVG": None, "STITCH_SUM": None, "pi": np.pi, "cos": np.cos, "sin": np.sin, "sqrt": np.sqrt, "ln": np.log, "rand": np.random.rand, "randn": np.random.randn, "sdiv": sdiv}


class _DivTransformer(ast.NodeTransformer):
    """
    Helper class to use sdiv everywhere

    This is a NodeTransformer that converts Div nodes into
    function nodes that call the sdiv function

    Modified from https://stackoverflow.com/a/51918098 by Aran-Fey

    """

    def visit_BinOp(self, node):
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)

        if not isinstance(node.op, ast.Div):
            node.left = lhs
            node.right = rhs
            return node

        name = ast.Name("sdiv", ast.Load())
        args = [lhs, rhs]
        kwargs = []
        return ast.Call(name, args, kwargs)


class _FunctionVisitor(ast.NodeVisitor):
    """
    Collects deduplicated dependency names and rejects unsupported calls
    """

    def __init__(self, fcn_str):
        self.fcn_str = fcn_str
        self.dep_list = []
        self.seen = set()

    def visit_Name(self, node):
        if node.id not in supported_functions and node.id not in self.seen:
            self.seen.add(node.id)
            self.dep_list.append(node.id)

    def visit_Call(self, node):
        assert isinstance(node.func, ast.Name) and node.func.id in supported_functions, f"Only calls to supported functions are allowed ({ast.unparse(node.func)} in {self.fcn_str} is not supported)"
        self.generic_visit(node)


def _build_positional_function(dep_list, body):
    """
    Wrap an expression AST in ``def _fcn(<deps>): return <body>``
    """

    args = ast.arguments(
        posonlyargs=[],
        args=[ast.arg(arg=name) for name in dep_list],
        vararg=None,
        kwonlyargs=[],
        kw_defaults=[],
        kwarg=None,
        defaults=[],
    )
    return ast.FunctionDef(name="_fcn", args=args, body=[ast.Return(value=body)], decorator_list=[])


@cache
def parse_function(fcn_str: str) -> tuple:
    """
    Parses a string into a positional-call optimized Python function

    This function takes in the string representation of a function e.g. ``'x+y'`` and returns
    a Python function object together with the deduplicated names of the quantities the function
    depends on. The returned function is intended to be called positionally in that order:

    >>> fcn, deps = atomica.parse_function("x+y")
    >>> deps
    ("x", "y")
    >>> fcn(2, 3)
    5

    Note that for security, only a subset of Python functions are allowed to be called. These
    are mainly mathematical operations such as ``max`` or ``exp``. A full listing can be found
    in ``function_parser.py``.

    A common usage pattern is to assemble a positional argument vector using the tuple of
    dependencies returned by ``parse_function``. For example:

    >>> args = [2, 2]
    >>> fcn(*args)
    4

    The generated function uses ordinary Python positional-or-keyword parameters, so keyword calls
    still work, but Atomica's model hot path calls it positionally.

    :param fcn_str: A string containing a single Python expression
    :return: A tuple containing a function, and a deduplicated tuple of dependencies required by the function

    """

    assert "__" not in fcn_str, "Cannot use double underscores in functions"
    assert len(fcn_str) < 1800  # Function string must be less than 1800 characters
    fcn_str = fcn_str.replace(":", "___")
    fcn_ast = ast.parse(fcn_str, mode="eval")
    fcn_ast = _DivTransformer().visit(fcn_ast)
    fcn_ast = ast.fix_missing_locations(fcn_ast)

    visitor = _FunctionVisitor(fcn_str)
    visitor.visit(fcn_ast)
    dep_list = tuple(visitor.dep_list)

    func_def = _build_positional_function(dep_list, fcn_ast.body)
    module = ast.fix_missing_locations(ast.Module(body=[func_def], type_ignores=[]))
    compiled_code = compile(module, filename="<ast>", mode="exec")
    namespace = {"__builtins__": {}, **supported_functions}
    exec(compiled_code, namespace)

    return namespace["_fcn"], dep_list


# Example usage below - This can be moved to documentation later.
if __name__ == "__main__":
    f_string = "exp(x)+y**2"
    fcn, dep_list = parse_function(f_string)
    print(dep_list)
    print(fcn(1, 2))
    print(fcn(x=1, y=3))  # Keyword calls still work, but the model hot path uses positional calls
