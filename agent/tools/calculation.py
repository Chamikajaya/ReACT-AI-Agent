import logging
import ast
import operator
from typing import Dict, Any, Union

from agent.tools.base import Tool
from agent.exceptions import ToolExecutionError

logger = logging.getLogger(__name__)

# Supported operators for safe evaluation - rather than using dangerous eval()
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,  # Unary subtraction
}

class SafeEval(ast.NodeVisitor):
    """
    Safe evaluator for mathematical expressions.
    Restricts operations to basic arithmetic to prevent code injection.
    """
    
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        if type(node.op) not in OPERATORS:
            raise ToolExecutionError(f"Unsupported operator: {type(node.op).__name__}")
        
        return OPERATORS[type(node.op)](left, right)
    
    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        
        if type(node.op) not in OPERATORS:
            raise ToolExecutionError(f"Unsupported unary operator: {type(node.op).__name__}")
        
        return OPERATORS[type(node.op)](operand)
    
    def visit_Num(self, node):
        return node.n
    
    def visit_Constant(self, node):
        # For Python 3.8+
        if isinstance(node.value, (int, float)):
            return node.value
        raise ToolExecutionError(f"Unsupported constant: {node.value}")
    
    def visit_Name(self, node):
        # Allow a few mathematical constants
        if node.id == 'pi':
            return 3.141592653589793
        if node.id == 'e':
            return 2.718281828459045
        raise ToolExecutionError(f"Unsupported variable: {node.id}")
    
    def generic_visit(self, node):
        raise ToolExecutionError(f"Unsupported expression type: {type(node).__name__}")

def safe_eval(expr: str) -> Union[int, float]:
    """
    Safely evaluate a mathematical expression.
    """
    try:
        node = ast.parse(expr, mode='eval').body
        return SafeEval().visit(node)
    except SyntaxError as e:
        raise ToolExecutionError(f"Syntax error in expression: {str(e)}")
    except Exception as e:
        raise ToolExecutionError(f"Error evaluating expression: {str(e)}")

class CalculationTool(Tool):
    """
    Tool to perform safe mathematical calculations.
    """
    
    def __init__(self):
        """Initialize the calculation tool."""
        super().__init__(
            name="calculate",
            description="Performs mathematical calculations. Usage: calculate: [expression]"
        )
    
    def execute(self, args: str) -> Dict[str, Any]:
        """
        Execute a calculation using the safe evaluator.
        
        Args:
            args: Mathematical expression string
            
        Returns:
            Dictionary with calculation result
        """
        expression = args.strip()
        
        try:
            result = safe_eval(expression)
            return {"result": result}
        except ToolExecutionError as e:
            logger.warning(f"Calculation error: {str(e)}")
            return {"error": f"Calculation error: {str(e)}"}