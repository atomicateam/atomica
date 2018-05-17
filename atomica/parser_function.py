import ast
import numpy as np

def parse_function(fcn_str):
    # Returns (fcn,dep_list)
    # Where dep_list corresponds to a list of keys for
    # the dict that needs to be passed to fcn()
    # supported_functions is a dict mapping ast names to functors imported in the namespace of this file
    assert ';' not in fcn_str # Cannot have more than one expression in the string
    assert '__' not in fcn_str # Cannot have double underscores...

    fcn_str = fcn_str.replace(':','___')
    supported_functions = {'exp':np.exp,'floor':np.floor}
    fcn_ast = ast.parse(fcn_str, mode='eval')
    dep_list = []
    for node in ast.walk(fcn_ast):
        if isinstance(node, ast.Name) and node.id not in supported_functions:
            dep_list.append(node.id)
        elif isinstance(node,ast.Call):
            assert node.func.id in supported_functions, "Only calls to supported functions are allowed"
    compiled_code = compile(fcn_ast,filename="<ast>", mode="eval")
    return (lambda deps: eval(compiled_code,deps,supported_functions),dep_list)

## Example usage below
if __name__ == '__main__':
    f_string = 'exp(x)+y**2'
    fcn,dep_list = parse_function(f_string)
    print(dep_list)
    deps = {'x':1,'y':2}
    print(fcn(deps))
    deps = {'x':1,'y':3}
    print(fcn(deps))

