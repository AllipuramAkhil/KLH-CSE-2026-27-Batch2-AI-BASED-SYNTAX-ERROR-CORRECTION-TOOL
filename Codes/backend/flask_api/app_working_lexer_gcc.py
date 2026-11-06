from flask import Flask, request, jsonify
import subprocess
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "AI Compiler Backend Running"


@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.get_json()

    code = data.get("code", "")
    language = data.get("language", "c")

    # =========================
    # LEXER SECTION
    # =========================

    lexer_dir = os.path.expanduser(
        "~/AI_Compiler_Assistant/lexer"
    )

    input_file = os.path.join(
        lexer_dir,
        "input.c"
    )

    with open(input_file, "w") as f:
        f.write(code)

    result = subprocess.run(
        ["./lexer"],
        cwd=lexer_dir,
        capture_output=True,
        text=True
    )

    lexer_output = result.stdout.strip()

    lexical_tokens = []

    for index, line in enumerate(
        lexer_output.split("\n"),
        start=1
    ):
        if ":" in line:

            parts = line.split(":")

            token_type = parts[0].strip()

            token_value = parts[1].strip()

            lexical_tokens.append({
                "number": index,
                "type": token_type,
                "value": token_value
            })

    # =========================
    # GCC ERROR DETECTION
    # =========================

    gcc_file = os.path.join(
        os.getcwd(),
        "temp.c"
    )

    with open(gcc_file, "w") as f:
        f.write(code)

    gcc_result = subprocess.run(
        ["gcc", gcc_file],
        capture_output=True,
        text=True
    )

    errors = []

    if gcc_result.returncode != 0:

        error_lines = gcc_result.stderr.split("\n")

        for line in error_lines:

            if "error:" in line:

                try:

                    parts = line.split(":")

                    line_number = parts[1]

                    column_number = parts[2]

                    error_message = ":".join(parts[3:])

                    error_message = error_message.replace(
                        "error:",
                        ""
                    ).strip()

                    # =========================
                    # AUTO FIX ACTION DETECTION
                    # =========================

                    action = "unknown"
                    target_line = int(line_number)

                    if (
                        "expected" in error_message
                        and ";" in error_message
                    ):
                        action = "add_semicolon"
                        target_line = int(line_number) - 1

                    elif (
                        "expected" in error_message
                        and ")" in error_message
                    ):
                        action = "add_parenthesis"

                    elif (
                        "expected" in error_message
                        and "}" in error_message
                    ):
                        action = "add_brace"

                    elif "undeclared" in error_message:
                        action = "declare_variable"

                    errors.append({
                        "line": line_number,
                        "column": column_number,
                        "type": "Syntax Error",
                        "message": error_message,
                        "action": action,
                        "targetLine": target_line
                    })

                except Exception:

                    errors.append({
                        "line": "Unknown",
                        "column": "Unknown",
                        "type": "Compiler Error",
                        "message": line,
                        "action": "unknown",
                        "targetLine": 0
                    })

    print("\n===== ERRORS =====")
    print(errors)
    print("==================\n")

    return jsonify({

        "success": True,

        "lexical": lexical_tokens,

        "parsing": {
            "matchedRules": [
                "Lexical Analysis Complete"
            ]
        },

        "errorDetection": errors,

        "aiSuggestion": {
            "correction":
                "Check compiler errors and apply fixes"
        }
    })


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )
