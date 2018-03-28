#%% Imports

from atomica.system import OptimaException, logger

from pyparsing import Word, Literal, Optional, alphanums, nums, ZeroOrMore, Group, Forward
import operator
from copy import deepcopy as dcp


#%% Parser for functions written as strings

class FunctionParser(object):
    """
    A parser that can decompose a string of numbers and variables into tokens, then evaluate the expression.
    Incorporates BODMAS operations, as well as exponentiation and negative numbers.
    Any modifications to this should be made with care, given the left-to-right parsing grammar.
    
    Script written by Paul McGuire ~2006 used as a basis.
    Accordingly, implementing further tokens (e.g. exponential functions) should search fourFn.py online.
    
    Version: 2016nov01
    """

    def __init__(self, debug = False):
        self.debug = debug      # Print out steps for string decomposition and evaluation.
        
        self.expr_stack = []    # A list for storing tokens in reverse evaluation order.
        self.var_dict = {}      # A dictionary for taking note of variable names in the function string.
        
        plus    = Literal("+")
        minus   = Literal("-")
        mult    = Literal("*")
        div     = Literal("/")
        neg     = Optional("-")
        addop  = plus | minus
        multop = mult | div
        expop = Literal("^")
        lpar  = Literal("(").suppress()
        rpar  = Literal(")").suppress()
        num = Word(nums + ".")
        var = Word(alphanums + "_")
        
        self.op_dict = {"+": operator.add,
                        "-": operator.sub,
                        "*": operator.mul,
                        "/": operator.truediv,
                        "^": operator.pow}
        
        self.grammar = Forward()
        primary = (neg + ((num | var.setParseAction(self.noteVariable)).setParseAction(self.pushFirst) | Group(lpar + self.grammar + rpar))).setParseAction(self.pushUnaryMinus)        
        factor = Forward()      # Making sure chain-exponentiation tokens are evaluated from right to left.
        factor << primary + ZeroOrMore((expop + factor).setParseAction(self.pushFirst))
        term = factor + ZeroOrMore((multop + factor).setParseAction(self.pushFirst))
        self.grammar << term + ZeroOrMore((addop + term).setParseAction(self.pushFirst))
        
    def pushFirst(self, s, loc, toks):
        """ Used to push tokens into an evaluation (FILO) stack. """
        self.expr_stack.append(toks[0])
        
    def pushUnaryMinus(self, s, loc, toks):
        """ Used to push a unary-minus token into an evaluation stack (i.e. a symbol denoting a negative number). """
        if toks and toks[0]=="-": 
            self.expr_stack.append("u-")
            
    def noteVariable(self, s, loc, toks):
        """ Used to keep track of variables in string (a.k.a. dependencies). """
        self.var_dict[toks[0]] = 0.0    # Set default values of 0.0, in case these values are used in immediate evaluation.
            
    def produceStack(self, string):
        """ Produces a list of tokens in FILO evaluation order. Also returns a dictionary of variable dependencies. """
        self.expr_stack = []
        self.var_dict = {}
        val = self.grammar.parseString(string)
        expr_stack = dcp(self.expr_stack)
        var_dict = dcp(self.var_dict)
        
        # Delete stack and variable dictioary attributes after processing, just in case.
        self.expr_stack = []
        self.var_dict = {}
        if self.debug:
            logger.debug("Token decomposition...")
            logger.debug(val)
            logger.debug("Token stack for evaluation...")
            logger.debug(expr_stack)
            logger.debug("Tokens that are variables...")
            logger.debug(var_dict.keys())
        
        return expr_stack, var_dict 
        
    def evaluateStack(self, stack, deps = None, level = None):
        """
        Recursively evaluates a stack produced from a string representing a mathematical function.
        The stack must have been produced in FILO order, where the last tokens (popped out) are evaluated first.
        A dictionary of dependencies (with values) must be provided as deps if there are variable names in the stack.
        """
        
        if level == None:
            if self.debug: logger.debug("Progressing through stack evaluation...")
            level = 0
        op = stack.pop()
        if op == "u-":
            return -self.evaluateStack(stack, deps = deps, level = level + 1)
        elif op in "+-*/^":
            op2 = self.evaluateStack(stack, deps = deps, level = level + 1)
            op1 = self.evaluateStack(stack, deps = deps, level = level + 1)
            if self.debug: logger.debug("Level {0}: {1} {2} {3} = {4}".format(level, op1, op, op2, self.op_dict[op](op1, op2)))
            return self.op_dict[op](op1, op2)
        elif op[0].isalpha():
            try:
                opval = deps[op]
            except:
                raise OptimaException("ERROR: Dependent variable '{0}' has not been provided a value via function parser.".format(op))
            return opval
        else:
            return float(op)
            
    def parse(self, string, deps = None):
        """
        Decomposes a string into a token stack and then evaluates it, using dictionary deps to give values to variables.
        For the sake of performance, it is recommended to separate stack production and evaluation in practice.
        """
        expr_stack, var_dict = self.produceStack(string)
        if not deps is None: var_dict = deps
        return self.evaluateStack(stack = expr_stack, deps = var_dict)