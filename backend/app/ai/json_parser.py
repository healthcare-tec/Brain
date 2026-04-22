"""
Robust JSON parser for LLM responses.

Large language models — especially local ones like gemma3:270m via Ollama —
often return JSON that is technically invalid:
  - Markdown fences (```json ... ```)
  - JavaScript-style comments (// line  or  /* block */)
  - Trailing commas in objects/arrays
  - Single-quoted strings instead of double-quoted
  - Explanatory text before or after the JSON object
  - Truncated output (model hit token limit mid-object)

parse_ai_json(text) tries each strategy in order and returns the first
successfully parsed dict/list, or raises ValueError with a diagnostic
message if all strategies fail.

is_template_response(text) detects when the model echoed the prompt
template instead of filling it in (common with smaller local models).
"""

import json
import re
import logging

logger = logging.getLogger(__name__)


# ── Strategy helpers ──────────────────────────────────────────────────────────

def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers."""
    # Match optional language tag after opening fence
    pattern = r"```(?:json|JSON|js|javascript)?\s*\n?(.*?)\n?```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Also handle single-backtick inline code blocks (rare but seen)
    pattern2 = r"`({.*?})`"
    match2 = re.search(pattern2, text, re.DOTALL)
    if match2:
        return match2.group(1).strip()
    return text


def _remove_js_comments(text: str) -> str:
    """Remove JavaScript-style // line comments and /* block */ comments."""
    # Block comments first (greedy, non-nested)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    # Line comments — but only outside string literals (simple heuristic)
    # We process line by line and strip anything after // that isn't inside quotes
    lines = []
    for line in text.splitlines():
        # Find // not inside a string (very simplified: just strip after first //)
        # This handles the common case; edge cases with URLs in strings are rare
        in_string = False
        i = 0
        result = []
        while i < len(line):
            ch = line[i]
            if ch == '"' and (i == 0 or line[i - 1] != "\\"):
                in_string = not in_string
            if not in_string and ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                break  # rest of line is a comment
            result.append(ch)
            i += 1
        lines.append("".join(result))
    return "\n".join(lines)


def _remove_trailing_commas(text: str) -> str:
    """Remove trailing commas before } or ] (common LLM mistake)."""
    # ,   followed by optional whitespace/newlines then } or ]
    return re.sub(r",\s*([}\]])", r"\1", text)


def _fix_single_quotes(text: str) -> str:
    """Replace single-quoted strings with double-quoted (best-effort)."""
    # This is intentionally conservative: only replace 'value' patterns
    # that look like JSON string values or keys.
    # Full single→double conversion is fragile; we only do it as a last resort.
    return re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", r'"\1"', text)


def _extract_first_json_object(text: str) -> str:
    """
    Extract the first complete {...} or [...] block from arbitrary text.
    Handles nested braces/brackets by counting depth.
    """
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        if start == -1:
            continue
        depth = 0
        for i, ch in enumerate(text[start:], start=start):
            if ch == start_char:
                depth += 1
            elif ch == end_char:
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return text


# ── Public API ────────────────────────────────────────────────────────────────

def parse_ai_json(text: str) -> dict | list:
    """
    Parse a JSON string returned by an LLM, applying multiple fallback
    strategies to handle common malformed output patterns.

    Strategies (applied in order):
      1. json.loads() on the raw text
      2. Strip markdown fences, then json.loads()
      3. Remove JS comments, then json.loads()
      4. Remove trailing commas, then json.loads()
      5. Extract first {...} / [...] block, then json.loads()
      6. All of the above combined + single-quote fix, then json.loads()

    Raises:
        ValueError: if all strategies fail, with a diagnostic message
                    that includes the last json.JSONDecodeError.
    """
    if not text or not text.strip():
        raise ValueError("Empty response from AI model")

    original = text.strip()
    last_error: Exception | None = None

    def _try(candidate: str) -> dict | list | None:
        nonlocal last_error
        candidate = candidate.strip()
        if not candidate:
            return None
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            last_error = e
            return None

    # Strategy 1: raw
    result = _try(original)
    if result is not None:
        return result
    logger.debug("parse_ai_json: strategy 1 (raw) failed: %s", last_error)

    # Strategy 2: strip markdown fences
    stripped = _strip_markdown_fences(original)
    if stripped != original:
        result = _try(stripped)
        if result is not None:
            logger.debug("parse_ai_json: strategy 2 (markdown fences) succeeded")
            return result
    logger.debug("parse_ai_json: strategy 2 (markdown fences) failed")

    # Strategy 3: remove JS comments
    no_comments = _remove_js_comments(stripped)
    result = _try(no_comments)
    if result is not None:
        logger.debug("parse_ai_json: strategy 3 (remove comments) succeeded")
        return result
    logger.debug("parse_ai_json: strategy 3 (remove comments) failed")

    # Strategy 4: remove trailing commas
    no_trailing = _remove_trailing_commas(no_comments)
    result = _try(no_trailing)
    if result is not None:
        logger.debug("parse_ai_json: strategy 4 (trailing commas) succeeded")
        return result
    logger.debug("parse_ai_json: strategy 4 (trailing commas) failed")

    # Strategy 5: extract first JSON object/array from surrounding text
    extracted = _extract_first_json_object(no_trailing)
    result = _try(extracted)
    if result is not None:
        logger.debug("parse_ai_json: strategy 5 (extract first block) succeeded")
        return result
    logger.debug("parse_ai_json: strategy 5 (extract first block) failed")

    # Strategy 6: everything combined + single-quote fix (most aggressive)
    aggressive = _fix_single_quotes(extracted)
    result = _try(aggressive)
    if result is not None:
        logger.debug("parse_ai_json: strategy 6 (single-quote fix) succeeded")
        return result
    logger.debug("parse_ai_json: strategy 6 (single-quote fix) failed")

    # All strategies exhausted
    preview = original[:200].replace("\n", "\\n")
    raise ValueError(
        f"Could not parse AI response as JSON after 6 strategies. "
        f"Last error: {last_error}. "
        f"Response preview: {preview!r}"
    )


# ── Template detection ────────────────────────────────────────────────────────

# These strings appear in prompt templates/schemas but should NEVER appear as
# actual values in a real AI response. If the parsed JSON contains any of them
# as a field value, the model echoed the template instead of filling it in.
_TEMPLATE_VALUE_MARKERS = [
    # classifier.py schema markers
    "task|project|note|idea|trash",
    "0.0-1.0",
    "concise title (max 80 chars)",
    "@work|@home|@computer|@phone|@errands|@waiting|@anywhere",
    "low|medium|high|critical",
    "null or integer",
    "one sentence explaining",
    # interpreter.py schema markers
    "the very next concrete physical action",
    "low|medium|high",
    "true|false",
    "who could do this, or null",
    # analyzer.py schema markers
    "positive|negative|neutral",
    "overestimates|underestimates|accurate|insufficient_data",
    "reversible|partially-reversible|irreversible",
    # Generic template indicators
    "description of the pattern",
    "what data supports this",
]


def is_template_response(text: str) -> bool:
    """
    Return True if the AI response appears to be an echoed prompt template
    rather than a real classification/analysis.

    Checks both the raw text and, if parseable, the JSON values.

    Args:
        text: Raw string returned by the AI model.

    Returns:
        True if the response looks like a template echo, False otherwise.
    """
    if not text:
        return False

    text_lower = text.lower()

    # Quick check on raw text — template markers are very distinctive
    for marker in _TEMPLATE_VALUE_MARKERS:
        if marker.lower() in text_lower:
            logger.debug("is_template_response: found marker %r in raw text", marker)
            return True

    # Also check parsed JSON values for template strings
    try:
        parsed = parse_ai_json(text)
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    for marker in _TEMPLATE_VALUE_MARKERS:
                        if marker.lower() in value_lower:
                            logger.debug(
                                "is_template_response: field %r has template value %r",
                                key, value[:80]
                            )
                            return True
    except (ValueError, Exception):
        pass  # If we can't parse it, the raw text check above is sufficient

    return False
