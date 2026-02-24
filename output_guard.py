import ast
import re
from typing import Tuple


def _strip_markdown_fences(text: str) -> str:
    """
    If model returns ```python ... ```, extract inside. Otherwise return as-is.
    """
    fence = re.search(r"```(?:python)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    return text.strip()


def _looks_like_python_tests(code: str) -> bool:
    """
    Ensure output is valid python and contains at least one test_ function.
    Restrict to:
      - imports
      - test functions
      - helper functions are not allowed (keeps strict)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    has_test = False
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.FunctionDef):
            if not node.name.startswith("test_"):
                return False
            has_test = True
            continue
        # allow module docstring? (we prefer none; disallow to be strict)
        return False

    return has_test


def normalize_and_validate_tests(raw: str) -> Tuple[bool, str]:
    """
    Returns (ok, normalized_text_or_error_message).
    """
    cleaned = _strip_markdown_fences(raw)

    # Remove any leading/trailing whitespace lines
    cleaned = "\n".join([ln.rstrip() for ln in cleaned.splitlines()]).strip() + "\n"

    if _looks_like_python_tests(cleaned):
    # Ensure pytest is imported if used
        if "pytest." in cleaned and "import pytest" not in cleaned:
            cleaned = "import pytest\n" + cleaned
        return True, cleaned

    # If invalid, attempt a small salvage: remove non-python leading lines until parse works
    lines = cleaned.splitlines()
    for i in range(min(8, len(lines))):
        candidate = "\n".join(lines[i:]).strip() + "\n"
        if _looks_like_python_tests(candidate):
            return True, candidate

    return False, "Error: Model output was not valid unit tests."