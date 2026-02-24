import ast
from typing import Optional, Tuple


SCOPE_ERROR = "Error: This tool only generates unit tests for functions."


def validate_single_function_source(source: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that source parses and contains exactly one top-level function.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False, SCOPE_ERROR

    funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(funcs) != 1:
        return False, SCOPE_ERROR

    # Also ensure it's really source code input, not "generate tests for X" etc.
    # If the module has only an Expr Constant string, it's likely not code.
    if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr) and isinstance(getattr(tree.body[0], "value", None), ast.Constant):
        return False, SCOPE_ERROR

    return True, None


def get_function_name(source: str) -> str:
    tree = ast.parse(source)
    funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return funcs[0].name