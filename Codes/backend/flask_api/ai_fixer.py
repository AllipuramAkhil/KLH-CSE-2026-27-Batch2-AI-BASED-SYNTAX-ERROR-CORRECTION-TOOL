import os

try:
    from .local_fixer import local_fix
except ImportError:
    from local_fixer import local_fix


def fix_code(code, language="c"):
    if not isinstance(code, str):
        raise TypeError("Source code must be a string.")

    language = language.lower()
    if language not in {"c", "cpp", "java", "python"}:
        raise ValueError(f"Unsupported language: {language}")

    if language in {"c", "cpp"}:
        fixed = local_fix(code)
        if fixed != code:
            return fixed

    try:
        from ollama import chat
    except ImportError as error:
        raise RuntimeError(
            "The local fixer found no correction and the optional Ollama "
            "dependency is unavailable."
        ) from error

    model = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:0.5b")
    response = chat(
        model=model,
        messages=[{
            "role": "user",
            "content": (
                f"Return only corrected {language} source code. Do not include "
                "Markdown fences or an explanation. Preserve the program's "
                f"intent and make only necessary corrections.\n\n{code}"
            ),
        }],
    )

    try:
        corrected = response["message"]["content"].strip()
    except (KeyError, TypeError) as error:
        raise RuntimeError(
            "The AI correction service returned an invalid response."
        ) from error

    if corrected.startswith("```"):
        corrected = corrected.split("\n", 1)[-1]
        if corrected.rstrip().endswith("```"):
            corrected = corrected.rstrip()[:-3].rstrip()

    if not corrected or corrected.strip() == code.strip():
        return code

    return corrected
