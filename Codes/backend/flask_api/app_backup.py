from flask import Flask, request, jsonify
import subprocess
import os
import re
from flask_cors import CORS
from ai_fixer import fix_code

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

LEXER_DIR = os.path.join(BASE_DIR, "lexer")
LEXER_EXE = os.path.join(LEXER_DIR, "lexer.exe")

GCC_PATH = r"C:\msys64\ucrt64\bin\gcc.exe"


def compile_c(source_file, output_file, timeout=15):
    if not os.path.isfile(GCC_PATH):
        raise FileNotFoundError(
            f"GCC not found: {GCC_PATH}"
        )

    return subprocess.run(
        [
            GCC_PATH,
            source_file,
            "-o",
            output_file
        ],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        timeout=timeout
    )


def parse_compiler_errors(stderr):
    errors = []

    pattern = re.compile(
        r"^(.+?):(\d+):(\d+):\s*"
        r"(fatal error|error|warning):\s*(.*)$"
    )

    for line in stderr.splitlines():
        match = pattern.match(line.strip())

        if not match:
            continue

        _, line_number, column_number, error_type, message = (
            match.groups()
        )

        action = "unknown"
        target_line = int(line_number)

        if "expected ';'" in message or 'expected ";"' in message:
            action = "add_semicolon"

        elif "expected ')'" in message or 'expected ")"' in message:
            action = "add_parenthesis"

        elif "expected '}'" in message or 'expected "}"' in message:
            action = "add_brace"

        elif "undeclared" in message:
            action = "declare_variable"

        errors.append({
            "line": int(line_number),
            "column": int(column_number),
            "type": (
                "Warning"
                if error_type == "warning"
                else "Syntax Error"
            ),
            "message": message,
            "action": action,
            "targetLine": target_line
        })

    return errors


@app.route("/")
def home():
    return "AI Compiler Backend Running"


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}

    code = data.get("code", "")
    language = data.get("language", "c")

    if not isinstance(code, str) or not code.strip():
        return jsonify({
            "success": False,
            "message": "Please enter C code."
        }), 400

    if str(language).lower() != "c":
        return jsonify({
            "success": False,
            "message": "Only C language is currently supported."
        }), 400

    source_file = os.path.join(
        BACKEND_DIR,
        "temp.c"
    )

    output_file = os.path.join(
        BACKEND_DIR,
        "temp.exe"
    )

    input_file = os.path.join(
        LEXER_DIR,
        "input.c"
    )

    try:
        # Create lexer directory if it does not exist
        os.makedirs(
            LEXER_DIR,
            exist_ok=True
        )

        # Save C code for GCC
        with open(
            source_file,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(code)

        # Save C code for lexer
        with open(
            input_file,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(code)

        # ---------------------------------
        # LEXICAL ANALYSIS
        # ---------------------------------

        lexical_tokens = []
        lexer_message = None

        if os.path.isfile(LEXER_EXE):

            lexer_result = subprocess.run(
                [LEXER_EXE],
                cwd=LEXER_DIR,
                input=code,
                capture_output=True,
                text=True,
                timeout=10
            )

            if lexer_result.returncode == 0:

                for line in lexer_result.stdout.splitlines():

                    if ":" in line:

                        token_type, token_value = line.split(
                            ":",
                            1
                        )

                        lexical_tokens.append({
                            "number": len(lexical_tokens) + 1,
                            "type": token_type.strip(),
                            "value": token_value.strip()
                        })

                if not lexical_tokens:
                    lexer_message = (
                        "No tokens parsed. "
                        "Check the lexer output format."
                    )

            else:
                lexer_message = (
                    lexer_result.stderr.strip()
                    or "Lexer execution failed."
                )

        else:
            lexer_message = (
                "lexer.exe not found. "
                "Compile lexer.l first."
            )

        # ---------------------------------
        # GCC COMPILATION
        # ---------------------------------

        gcc_result = compile_c(
            source_file,
            output_file
        )

        # Print complete GCC information
        # This appears in Flask terminal.
        print("\n========== GCC RESULT ==========")
        print("Return Code:", gcc_result.returncode)
        print("STDOUT:", repr(gcc_result.stdout))
        print("STDERR:", repr(gcc_result.stderr))
        print("================================\n")

        # Parse GCC errors
        errors = parse_compiler_errors(
            gcc_result.stderr
        )

        # If GCC failed but our parser could not
        # understand the GCC error, preserve the
        # complete GCC output.
        if gcc_result.returncode != 0 and not errors:

            errors.append({
                "line": "Unknown",
                "column": "Unknown",
                "type": "Compilation Error",
                "message": (
                    f"GCC exited with code "
                    f"{gcc_result.returncode}. "
                    f"stdout: {gcc_result.stdout!r}; "
                    f"stderr: {gcc_result.stderr!r}"
                ),
                "action": "unknown",
                "targetLine": 0
            })

        # ---------------------------------
        # RESPONSE
        # ---------------------------------

        return jsonify({
            "success": True,

            "lexical": lexical_tokens,

            "lexerMessage": lexer_message,

            "parsing": {
                "matchedRules": [
                    "Lexical Analysis Complete"
                ],
                "message": (
                    "Full parser not implemented yet."
                )
            },

            "semantic": {
                "result": "Not implemented"
            },

            "symbolTable": [],

            "intermediateCode": [],

            "optimization": [],

            "codeGeneration": [],

            "errorDetection": errors,

            "compilation": {
                "success": (
                    gcc_result.returncode == 0
                ),
                "message": (
                    "Compilation successful."
                    if gcc_result.returncode == 0
                    else "Compilation failed."
                ),

                # Added for debugging
                "returnCode": gcc_result.returncode,
                "stdout": gcc_result.stdout,
                "stderr": gcc_result.stderr
            },

            "aiSuggestion": {
                "correction": (
                    "Review the compiler errors "
                    "and use Apply Fix if needed."
                )
            }
        })

    except subprocess.TimeoutExpired:

        return jsonify({
            "success": False,
            "message": (
                "Compiler operation timed out."
            )
        }), 500

    except Exception as e:

        app.logger.exception(
            "Analysis failed"
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/run", methods=["POST"])
def run_code():

    data = request.get_json(silent=True) or {}

    code = data.get("code", "")
    user_input = data.get("input", "")

    if not isinstance(code, str) or not code.strip():

        return jsonify({
            "success": False,
            "output": "Please enter C code."
        }), 400

    source_file = os.path.join(
        BACKEND_DIR,
        "temp_run.c"
    )

    output_file = os.path.join(
        BACKEND_DIR,
        "temp_run.exe"
    )

    try:

        with open(
            source_file,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(code)

        # Compile code
        compile_result = compile_c(
            source_file,
            output_file
        )

        # Debug compilation result
        print("\n========== RUN COMPILE RESULT ==========")
        print(
            "Return Code:",
            compile_result.returncode
        )
        print(
            "STDOUT:",
            repr(compile_result.stdout)
        )
        print(
            "STDERR:",
            repr(compile_result.stderr)
        )
        print("========================================\n")

        if compile_result.returncode != 0:

            return jsonify({
                "success": False,
                "output": (
                    compile_result.stderr.strip()
                    or "Compilation failed."
                ),
                "returnCode": (
                    compile_result.returncode
                )
            })

        # Run compiled program
        run_result = subprocess.run(
            [os.path.abspath(output_file)],
            cwd=BACKEND_DIR,
            input=(
                user_input
                if isinstance(user_input, str)
                else str(user_input)
            ),
            capture_output=True,
            text=True,
            timeout=5
        )

        return jsonify({
            "success": (
                run_result.returncode == 0
            ),
            "output": run_result.stdout,
            "error": run_result.stderr,
            "returnCode": (
                run_result.returncode
            )
        })

    except subprocess.TimeoutExpired:

        return jsonify({
            "success": False,
            "output": (
                "Program execution timed out."
            )
        }), 408

    except Exception as e:

        app.logger.exception(
            "Code execution failed"
        )

        return jsonify({
            "success": False,
            "output": str(e)
        }), 500


@app.route("/fix", methods=["POST"])
def fix():

    data = request.get_json(silent=True) or {}

    code = data.get("code", "")

    if not isinstance(code, str) or not code.strip():

        return jsonify({
            "success": False,
            "message": (
                "Please enter code to fix."
            ),
            "fixedCode": (
                code
                if isinstance(code, str)
                else ""
            )
        }), 400

    try:

        fixed_code = fix_code(code)

        return jsonify({
            "success": True,
            "fixedCode": fixed_code
        })

    except Exception as e:

        app.logger.exception(
            "AI fix failed"
        )

        return jsonify({
            "success": False,
            "message": str(e),
            "fixedCode": code
        }), 500


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        debug=True,
        port=5000
    )