import argparse
import sys
from pathlib import Path

from app.prompts import SYSTEM_PROMPT
from app.validate import validate_single_function_source, get_function_name, SCOPE_ERROR
from app.sanitize import sanitize_source, extract_single_function_source
from app.llm_client import OpenAICompatibleClient, LLMClientError
from app.output_guard import normalize_and_validate_tests


def _read_input_code(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def build_messages(function_name: str, sanitized_function_source: str) -> list[dict]:
    user_prompt = (
        "Generate pytest unit tests for the following Python function.\n\n"
        f"Function name: {function_name}\n\n"
        "SOURCE (single function):\n"
        f"{sanitized_function_source}\n"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def cmd_generate(args: argparse.Namespace) -> int:
    source = _read_input_code(args.file)

    ok, err = validate_single_function_source(source)
    if not ok:
        # Scope errors must be exactly returned (use stdout)
        sys.stdout.write(err + "\n")
        return 0

    # Extract single function snippet from original source for better focus
    try:
        fn_name, fn_src = extract_single_function_source(source)
    except Exception:
        sys.stdout.write(SCOPE_ERROR + "\n")
        return 0

    # Sanitize to reduce prompt injection in comments/docstrings
    sanitized = sanitize_source(fn_src)

    # LLM call
    try:
        client = OpenAICompatibleClient()
        messages = build_messages(fn_name, sanitized)
        raw = client.chat_completions(messages=messages, temperature=0.0, max_tokens=args.max_tokens)
    except LLMClientError as e:
        # Any operational error goes to stderr, not stdout
        sys.stderr.write(f"Error: LLM request failed: {e}\n")
        return 1

    # Enforce strict “tests only”
    ok_out, out = normalize_and_validate_tests(raw)
    if not ok_out:
        sys.stderr.write(out + "\n")
        return 1

    # Tests MUST go to stdout ONLY
    sys.stdout.write(out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="unit-test-gen",
        description="Generate pytest unit tests for a single provided Python function (LLM-backed).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="Generate tests for a single-function Python source input.")
    g.add_argument("-f", "--file", help="Path to a .py file containing a single function. If omitted, reads from stdin.")
    g.add_argument("--max-tokens", type=int, default=900, help="Max tokens for LLM output.")
    g.set_defaults(func=cmd_generate)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())