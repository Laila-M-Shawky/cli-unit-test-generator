import ast
import io
import tokenize
from typing import Tuple


def strip_comments(source: str) -> str:
    """
    Remove comments using tokenize while preserving code structure.
    """
    out_tokens = []
    reader = io.StringIO(source).readline
    try:
        for tok in tokenize.generate_tokens(reader):
            tok_type, tok_str, start, end, line = tok
            if tok_type == tokenize.COMMENT:
                continue
            out_tokens.append((tok_type, tok_str))
        return tokenize.untokenize(out_tokens)
    except tokenize.TokenError:
        # If tokenization fails, return original (validation will likely catch issues).
        return source


class _DocstringStripper(ast.NodeTransformer):
    def _strip_docstring_from_body(self, body):
        if not body:
            return body
        first = body[0]
        # Docstring is typically an Expr node containing a Constant string
        if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant):
            if isinstance(first.value.value, str):
                return body[1:]
        return body

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.generic_visit(node)
        node.body = self._strip_docstring_from_body(node.body)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.generic_visit(node)
        node.body = self._strip_docstring_from_body(node.body)
        return node

    def visit_Module(self, node: ast.Module):
        self.generic_visit(node)
        node.body = self._strip_docstring_from_body(node.body)
        return node


def strip_docstrings(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source
    tree = _DocstringStripper().visit(tree)
    ast.fix_missing_locations(tree)
    try:
        # Python 3.9+ has ast.unparse
        return ast.unparse(tree)
    except Exception:
        return source


def sanitize_source(source: str) -> str:
    """
    Defense-in-depth sanitization:
    - Strip comments (common injection vector)
    - Strip docstrings (another injection vector)
    """
    no_comments = strip_comments(source)
    no_docstrings = strip_docstrings(no_comments)
    return no_docstrings


def extract_single_function_source(original_source: str) -> Tuple[str, str]:
    """
    Returns (function_name, function_source_as_text) for the single top-level function.
    Uses AST line ranges; if line info missing, falls back to original.
    """
    tree = ast.parse(original_source)
    funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(funcs) != 1:
        raise ValueError("Expected exactly one function definition.")
    fn = funcs[0]
    name = fn.name

    # Extract exact lines from original source using lineno/end_lineno
    if hasattr(fn, "lineno") and hasattr(fn, "end_lineno") and fn.lineno and fn.end_lineno:
        lines = original_source.splitlines()
        snippet = "\n".join(lines[fn.lineno - 1 : fn.end_lineno])
        return name, snippet

    return name, original_source