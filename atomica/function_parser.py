"""
Implements the parameter function parser

Parameter functions are entered as strings in the Framework file.
This module implements the function parser that converts the string into
an executable Python representation.

"""

import ast
import numpy as np

# Only calls to functions in the dict below will be permitted
supported_functions = {
    'max': np.maximum,
    'min': np.minimum,
    'exp': np.exp,
    'floor': np.floor,
    'SRC_POP_AVG': None,
    'TGT_POP_AVG': None,
    'SRC_POP_SUM': None,
    'TGT_POP_SUM': None,
    'pi': np.pi,
    'cos': np.cos,
    'sin': np.sin,
    'sqrt': np.sqrt,
    'ln': np.log,
    'rand': np.random.rand,
    'randn': np.random.randn,
}


def parse_function(fcn_str: str) -> tuple:
    """
    Parses a string into a Python function

    This function takes in the string representation of a function e.g. ``'x+y'``. It
    returns an Python function object that takes in a keyword arguments corresponding to the
    original quantities that appeared in the function. For example:

    >>> fcn, deps = atomica.parse_function('x+y')
    >>> fcn
    <function atomica.function_parser.parse_function.<locals>.fcn(**deps)>
    >>> deps
    ['x', 'y']
    >>> fcn(x=2,y=3)
    5

    Note that for security, only a subset of Python functions are allowed to be called. These
    are mainly mathematical operations such as ``max`` or ``exp``. A full listing can be found
    in ``function_parser.py``.

    A common usage pattern is to construct a dict of inputs to the parsed function using the list
    of dependencies returned by ``parse_function``. For example:

    >>> argdict = dict.fromkeys(deps,2)
    >>> fcn(**argdict)
    4

    :param fcn_str: A string containing a single Python expression
    :return: A tuple containing a function, and a list of arguments required by the function

    """

    # Returns (fcn,dep_list)
    # Where dep_list corresponds to a list of keys for
    # the dict that needs to be passed to fcn()
    # supported_functions is a dict mapping ast names to functors imported in the namespace of this file
    assert '__' not in fcn_str, 'Cannot use double underscores in functions'
    assert len(fcn_str) < 1800  # Function string must be less than 1800 characters
    fcn_str = fcn_str.replace(':', '___')
    fcn_ast = ast.parse(fcn_str, mode='eval')
    dep_list = []
    for node in ast.walk(fcn_ast):
        if isinstance(node, ast.Name) and node.id not in supported_functions:
            dep_list.append(node.id)
        elif isinstance(node, ast.Call) and hasattr(node, 'func') and hasattr(node.func, 'id'):
            assert node.func.id in supported_functions, "Only calls to supported functions are allowed"
    compiled_code = compile(fcn_ast, filename="<ast>", mode="eval")

    def fcn(**deps):
        return eval(compiled_code, deps, supported_functions)

    return fcn, dep_list


# Example usage below - This can be moved to documentation later.
if __name__ == '__main__':
    f_string = 'exp(x)+y**2'
    fcn, dep_list = parse_function(f_string)
    print(dep_list)
    deps = {'x': 1, 'y': 2}
    print(fcn(**deps))
    print(fcn(x=1, y=3))  # The use of **deps means you can write out keyword arguments for `fcn` directly
