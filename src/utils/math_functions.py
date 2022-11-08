import ast
import operator as op

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.USub: op.neg,
             ast.UAdd: op.pos}


def eval_arithmetic_expression(expression: str):
    """
    >>> eval_arithmetic_expression('15+2')
    17
    >>> eval_arithmetic_expression('15-2')
    13
    >>> eval_arithmetic_expression('15*2')
    30
    >>> eval_arithmetic_expression('15/2')
    7.5
    >>> eval_arithmetic_expression('-15+2')
    -13
    >>> eval_arithmetic_expression('+15-2')
    13
    """
    return __eval(ast.parse(expression, mode='eval').body)


def eval_arithmetic_equation(equation: str):
    """
    >>> eval_arithmetic_equation('x+2=17')
    15
    >>> eval_arithmetic_equation('x-2=13')
    15
    >>> eval_arithmetic_equation('x*2=30')
    15
    >>> eval_arithmetic_equation('x/2=7.5')
    15
    >>> eval_arithmetic_equation('-x+2=13')
    15
    >>> eval_arithmetic_equation('+x-2=13')
    15
    """
    equation = f'{equation.replace(" ", "").replace("=", "-(")})'
    equation = equation.replace('x', '1j')
    result = __eval(ast.parse(equation, mode='eval').body)
    value = (-result.real / result.imag)
    if value in (-0, +0):
        return 0
    return value


def __eval(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](__eval(node.left), __eval(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](__eval(node.operand))
    else:
        raise TypeError(node)
