# tools/calculator_tool.py
from langchain_core.tools import tool

@tool
def calculate(expression: str) -> str:
    """
    Perform mathematical calculations.
    Use when user asks to calculate, compute, or do math.
    
    Args:
        expression: Math expression like '2+2', '100*0.15', '(500-300)/200*100'
    """
    try:
        # Safe eval — sirf math operations allowed
        allowed = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "pow": pow,
        }
        result = eval(expression, allowed)
        return f"Result: {expression} = {result}"

    except ZeroDivisionError:
        return "Error: Division by zero!"
    except Exception as e:
        return f"Calculation error: {e}"