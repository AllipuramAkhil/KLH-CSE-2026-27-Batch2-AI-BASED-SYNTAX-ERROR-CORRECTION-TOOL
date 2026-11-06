import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

try:
    from .ai_fixer import fix_code
except ImportError:
    from ai_fixer import fix_code


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:5174",
                "http://127.0.0.1:5174",
            ]
        }
    },
)

PROJECT_DIR = Path(__file__).resolve().parents[2]
LEXER_EXE = PROJECT_DIR / "lexer" / "lexer.exe"
GCC_CANDIDATES = (Path(r"C:\msys64\ucrt64\bin\gcc.exe"),)
GXX_CANDIDATES = (Path(r"C:\msys64\ucrt64\bin\g++.exe"),)
FLEX_CANDIDATES = (Path(r"C:\msys64\usr\bin\flex.exe"),)
PROCESS_TIMEOUT_SECONDS = 15
SUPPORTED_LANGUAGES = {"c", "cpp", "java", "python"}


class ToolUnavailableError(Exception):
    pass


def find_tool(name, candidates=()):
    executable = shutil.which(name)
    if executable:
        return executable

    for candidate in candidates:
        candidate_path = Path(candidate)
        if candidate_path.is_file():
            return str(candidate_path)

    java_home = os.environ.get("JAVA_HOME")
    if name in {"java", "javac"} and java_home:
        candidate_path = Path(java_home) / "bin" / (
            f"{name}.exe" if os.name == "nt" else name
        )
        if candidate_path.is_file():
            return str(candidate_path)

    if name in {"java", "javac"} and os.name == "nt":
        for root in (
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
        ):
            for candidate_path in root.glob(
                f"Eclipse Adoptium/jdk-*/bin/{name}.exe"
            ):
                if candidate_path.is_file():
                    return str(candidate_path)

    return None


def parse_compiler_errors(diagnostic_output):
    errors = []
    gcc_pattern = re.compile(
        r"^(.*?):(\d+):(\d+):\s*(fatal error|error|warning|note):\s*(.*)$"
    )
    javac_pattern = re.compile(
        r"^(.*?):(\d+):\s*(error|warning):\s*(.*)$"
    )

    lines = diagnostic_output.splitlines()
    for index, line in enumerate(lines):
        match = gcc_pattern.match(line.strip())
        if match:
            file_path, line_number, column_number, severity, message = (
                match.groups()
            )
        else:
            match = javac_pattern.match(line.strip())
            if not match:
                continue

            file_path, line_number, severity, message = match.groups()
            column_number = None
            for caret_line in lines[index + 1:index + 3]:
                caret_match = re.match(r"^\s*\^\s*$", caret_line)
                if caret_match:
                    column_number = len(caret_line) - len(
                        caret_line.lstrip()
                    ) + 1
                    break

        errors.append({
            "file": file_path,
            "line": int(line_number),
            "column": int(column_number) if column_number is not None else None,
            "type": severity,
            "severity": (
                "error"
                if severity in {"error", "fatal error"}
                else severity
            ),
            "message": message,
        })

    return errors


def parse_lexer_output(output):
    tokens = []
    pattern = re.compile(r"^\s*([A-Z_]+)\s*:\s*(.*?)\s*$")

    for line in output.splitlines():
        match = pattern.match(line)
        if not match:
            continue

        token_type, value = match.groups()
        tokens.append({
            "number": len(tokens) + 1,
            "type": token_type,
            "value": value,
        })

    return tokens


def tool_environment(tool):
    environment = os.environ.copy()
    if os.name == "nt":
        tool_dir = Path(tool).resolve().parent
        runtime_dirs = [str(tool_dir)]
        for runtime_dir in (
            Path(r"C:\msys64\ucrt64\bin"),
            Path(r"C:\msys64\usr\bin"),
        ):
            if runtime_dir.is_dir() and str(runtime_dir) not in runtime_dirs:
                runtime_dirs.append(str(runtime_dir))
        msys_bin = tool_dir.parent.parent / "usr" / "bin"
        if msys_bin.is_dir():
            if str(msys_bin) not in runtime_dirs:
                runtime_dirs.append(str(msys_bin))
        existing_path = environment.get("PATH", "")
        environment["PATH"] = os.pathsep.join(
            runtime_dirs + ([existing_path] if existing_path else [])
        )
    return environment


def execution_environment(language, tool=None):
    allowed_keys = (
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "PATHEXT",
    )
    environment = {
        key: os.environ[key]
        for key in allowed_keys
        if key in os.environ
    }

    path_entries = []
    if tool:
        tool_dir = Path(tool).resolve().parent
        path_entries.append(str(tool_dir))
        if language in {"c", "cpp"}:
            msys_bin = tool_dir.parent.parent / "usr" / "bin"
            if msys_bin.is_dir():
                path_entries.append(str(msys_bin))

    if os.name == "nt":
        system_root = environment.get("SYSTEMROOT", r"C:\Windows")
        path_entries.append(str(Path(system_root) / "System32"))

    if language == "python":
        path_entries.insert(0, str(Path(sys.executable).resolve().parent))
        environment["PYTHONIOENCODING"] = "utf-8"

    environment["PATH"] = os.pathsep.join(path_entries)
    return environment


def compile_native(language, source_file, output_file):
    if language == "c":
        tool = find_tool("gcc", GCC_CANDIDATES)
        compiler_name = "GCC"
    else:
        tool = find_tool("g++", GXX_CANDIDATES)
        compiler_name = "G++"

    if not tool:
        raise ToolUnavailableError(
            f"{compiler_name} was not found. Install it or add it to PATH."
        )

    return subprocess.run(
        [tool, str(source_file), "-o", str(output_file)],
        cwd=str(source_file.parent),
        capture_output=True,
        text=True,
        errors="replace",
        timeout=PROCESS_TIMEOUT_SECONDS,
        env=tool_environment(tool),
    )


def java_class_name(code):
    match = re.search(
        r"\b(?:public\s+)?class\s+([A-Za-z_$][A-Za-z0-9_$]*)",
        code,
    )
    return match.group(1) if match else "Main"


def compile_java(code, work_dir):
    javac = find_tool("javac")
    java = find_tool("java")
    if not javac or not java:
        raise ToolUnavailableError(
            "A Java JDK (javac and java) was not found. Install a JDK and add "
            "its bin directory to PATH or set JAVA_HOME."
        )

    class_name = java_class_name(code)
    source_file = work_dir / f"{class_name}.java"
    source_file.write_text(code, encoding="utf-8")
    result = subprocess.run(
        [javac, "-d", str(work_dir), str(source_file)],
        cwd=str(work_dir),
        capture_output=True,
        text=True,
        errors="replace",
        timeout=PROCESS_TIMEOUT_SECONDS,
        env=tool_environment(LEXER_EXE),
    )
    return result, [java, "-cp", str(work_dir), class_name]


def validate_correction(code, language):
    with tempfile.TemporaryDirectory(prefix="ai-compiler-fix-") as temp:
        work_dir = Path(temp)

        if language == "python":
            try:
                compile(code, str(work_dir / "program.py"), "exec")
            except SyntaxError as error:
                raise ValueError(
                    f"line {error.lineno}: {error.msg}"
                ) from error
            return

        if language == "java":
            result, _ = compile_java(code, work_dir)
        else:
            suffix = ".c" if language == "c" else ".cpp"
            source_file = work_dir / f"program{suffix}"
            output_file = work_dir / (
                "program.exe" if os.name == "nt" else "program"
            )
            source_file.write_text(code, encoding="utf-8")
            result = compile_native(language, source_file, output_file)

        if result.returncode != 0:
            details = result.stderr.strip() or result.stdout.strip()
            raise ValueError(
                details or f"The proposed {language.upper()} code did not compile."
            )


def as_text(value):
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value or ""


def failed_compilation(language, return_code, stdout, stderr, source_file):
    diagnostics = parse_compiler_errors(stderr + ("\n" + stdout if stdout else ""))
    if return_code != 0 and not diagnostics:
        details = "\n".join(part for part in (stderr.strip(), stdout.strip()) if part)
        message = (
            f"Compiler exited with code {return_code} without a parsed "
            f"diagnostic."
        )
        if details:
            message = f"{message}\n{details}"
        diagnostics.append({
            "file": str(source_file),
            "line": None,
            "column": None,
            "type": "compilation",
            "severity": "error",
            "message": message,
        })

    return {
        "success": return_code == 0,
        "language": language,
        "returnCode": return_code,
        "stdout": stdout,
        "stderr": stderr,
        "message": (
            f"{language.upper()} compilation succeeded."
            if return_code == 0
            else f"{language.upper()} compilation failed."
        ),
    }, diagnostics


def analyze_lexer(code):
    if not LEXER_EXE.is_file():
        return [], {
            "success": False,
            "message": f"Lexer executable was not found: {LEXER_EXE}",
            "returnCode": None,
        }

    try:
        with tempfile.TemporaryDirectory(prefix="ai-compiler-lexer-") as temp:
            work_dir = Path(temp)
            (work_dir / "input.c").write_text(code, encoding="utf-8")
            result = subprocess.run(
                [str(LEXER_EXE)],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                errors="replace",
                timeout=PROCESS_TIMEOUT_SECONDS,
            )

        tokens = parse_lexer_output(result.stdout)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            message = message or f"Lexer exited with code {result.returncode}."
            return tokens, {
                "success": False,
                "message": message,
                "returnCode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        if not tokens:
            return [], {
                "success": False,
                "message": (
                    "Lexer completed but produced no recognizable tokens."
                ),
                "returnCode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        return tokens, {
            "success": True,
            "message": "Lexical analysis completed.",
            "returnCode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return [], {
            "success": False,
            "message": "Lexical analysis timed out.",
            "returnCode": None,
        }
    except OSError as error:
        app.logger.exception("Unable to run the lexer")
        return [], {
            "success": False,
            "message": f"Unable to run lexer.exe: {error}",
            "returnCode": None,
        }


def request_data():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({
            "success": False,
            "message": "Request body must be a JSON object.",
            "error": "Invalid JSON request body.",
        }), 400)

    code = data.get("code")
    if not isinstance(code, str) or not code.strip():
        return None, (jsonify({
            "success": False,
            "message": "Please provide source code.",
            "error": "Source code is required.",
        }), 400)

    language = data.get("language", "c")
    if not isinstance(language, str) or language.lower() not in SUPPORTED_LANGUAGES:
        return None, (jsonify({
            "success": False,
            "message": "Unsupported language. Choose C, C++, Java, or Python.",
            "error": "Unsupported language.",
        }), 400)

    return {
        "code": code,
        "language": language.lower(),
        "input": data.get("input", ""),
    }, None


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "AI Compiler Backend Running",
        "tools": {
            "gcc": find_tool("gcc", GCC_CANDIDATES),
            "g++": find_tool("g++", GXX_CANDIDATES),
            "javac": find_tool("javac"),
            "java": find_tool("java"),
            "python": sys.executable if Path(sys.executable).is_file() else None,
            "flex": find_tool("flex", FLEX_CANDIDATES),
            "lexer": str(LEXER_EXE) if LEXER_EXE.is_file() else None,
        },
    })


@app.errorhandler(RequestEntityTooLarge)
def request_too_large(_error):
    return jsonify({
        "success": False,
        "message": "Request body exceeds the 1 MiB limit.",
        "error": "Request too large.",
    }), 413


@app.route("/analyze", methods=["POST"])
def analyze():
    data, error_response = request_data()
    if error_response:
        return error_response

    code = data["code"]
    language = data["language"]
    tokens = []
    lexer_status = {
        "success": False,
        "message": f"Lexical analysis is not implemented for {language}.",
        "returnCode": None,
    }

    try:
        with tempfile.TemporaryDirectory(prefix="ai-compiler-analyze-") as temp:
            work_dir = Path(temp)
            suffix = {"c": ".c", "cpp": ".cpp", "java": ".java"}[language] \
                if language != "python" else ".py"
            source_file = work_dir / f"source{suffix}"
            source_file.write_text(code, encoding="utf-8")

            if language == "c":
                tokens, lexer_status = analyze_lexer(code)
                executable = work_dir / (
                    "program.exe" if os.name == "nt" else "program"
                )
                result = compile_native(language, source_file, executable)
                compilation, diagnostics = failed_compilation(
                    language,
                    result.returncode,
                    result.stdout,
                    result.stderr,
                    source_file,
                )
            elif language == "cpp":
                executable = work_dir / (
                    "program.exe" if os.name == "nt" else "program"
                )
                result = compile_native(language, source_file, executable)
                compilation, diagnostics = failed_compilation(
                    language,
                    result.returncode,
                    result.stdout,
                    result.stderr,
                    source_file,
                )
            elif language == "java":
                result, _ = compile_java(code, work_dir)
                compilation, diagnostics = failed_compilation(
                    language,
                    result.returncode,
                    result.stdout,
                    result.stderr,
                    source_file,
                )
            else:
                try:
                    compile(code, str(source_file), "exec")
                    compilation = {
                        "success": True,
                        "language": language,
                        "returnCode": 0,
                        "stdout": "",
                        "stderr": "",
                        "message": "Python syntax check succeeded.",
                    }
                    diagnostics = []
                except SyntaxError as error:
                    message = error.msg
                    if error.text:
                        message = f"{message}: {error.text.strip()}"
                    diagnostics = [{
                        "file": error.filename,
                        "line": error.lineno,
                        "column": error.offset,
                        "type": "syntax error",
                        "severity": "error",
                        "message": message,
                    }]
                    compilation = {
                        "success": False,
                        "language": language,
                        "returnCode": 1,
                        "stdout": "",
                        "stderr": message,
                        "message": "Python syntax check failed.",
                    }

        compilation["diagnostics"] = diagnostics
        return jsonify({
            "success": compilation["success"],
            "output": compilation["stdout"],
            "error": compilation["stderr"],
            "message": compilation["message"],
            "returnCode": compilation["returnCode"],
            "lexical": tokens,
            "lexicalAnalysis": lexer_status,
            "errorDetection": diagnostics,
            "compilation": compilation,
            "parsing": {
                "implemented": False,
                "matchedRules": [],
                "message": "Parsing is not implemented.",
            },
            "semantic": {
                "implemented": False,
                "result": "Semantic analysis is not implemented.",
            },
            "symbolTable": ["Symbol table generation is not implemented."],
            "intermediateCode": [
                "Intermediate-code generation is not implemented."
            ],
            "optimization": ["Optimization is not implemented."],
            "codeGeneration": [
                "No separate project-owned target-code-generation stage is "
                "implemented. C/C++/Java target output is generated by the "
                "external compiler as part of compilation; Python is interpreted."
            ],
            "aiSuggestion": {
                "correction": (
                    "Select Apply Fix to request a code correction."
                )
            },
        })
    except ToolUnavailableError as error:
        app.logger.warning("Analysis tool unavailable: %s", error)
        return jsonify({
            "success": False,
            "output": "",
            "error": str(error),
            "message": str(error),
            "returnCode": None,
            "lexical": tokens,
            "lexicalAnalysis": lexer_status,
            "errorDetection": [{
                "file": None,
                "line": None,
                "column": None,
                "type": "tool unavailable",
                "severity": "error",
                "message": str(error),
            }],
            "compilation": {
                "success": False,
                "language": language,
                "returnCode": None,
                "stdout": "",
                "stderr": str(error),
                "message": str(error),
            },
        }), 503
    except subprocess.TimeoutExpired as error:
        app.logger.warning("Analysis timed out for %s", language)
        detail = (
            error.stderr.decode(errors="replace")
            if isinstance(error.stderr, bytes)
            else error.stderr or ""
        )
        message = f"Compiler operation timed out after {PROCESS_TIMEOUT_SECONDS} seconds."
        return jsonify({
            "success": False,
            "output": as_text(error.stdout),
            "error": detail or message,
            "message": message,
            "returnCode": None,
            "lexical": tokens,
            "lexicalAnalysis": lexer_status,
            "errorDetection": [{
                "file": None,
                "line": None,
                "column": None,
                "type": "timeout",
                "severity": "error",
                "message": message,
            }],
            "compilation": {
                "success": False,
                "language": language,
                "returnCode": None,
                "stdout": as_text(error.stdout),
                "stderr": detail,
                "message": message,
            },
        }), 408
    except OSError:
        app.logger.exception("Analysis failed")
        return jsonify({
            "success": False,
            "output": "",
            "error": "An operating-system error prevented analysis. See the backend log for details.",
            "message": "An operating-system error prevented analysis. See the backend log for details.",
            "returnCode": None,
            "lexical": tokens,
            "lexicalAnalysis": lexer_status,
            "errorDetection": [],
            "compilation": {
                "success": False,
                "language": language,
                "returnCode": None,
                "stdout": "",
                "stderr": "An operating-system error prevented analysis. See the backend log for details.",
                "message": "An operating-system error prevented analysis. See the backend log for details.",
            },
        }), 500


@app.route("/run", methods=["POST"])
def run_code():
    data, error_response = request_data()
    if error_response:
        return error_response

    code = data["code"]
    language = data["language"]
    user_input = data["input"]
    if not isinstance(user_input, str):
        return jsonify({
            "success": False,
            "output": "",
            "error": "Program input must be a string.",
            "message": "Program input must be a string.",
            "errorType": "request",
            "returnCode": None,
        }), 400

    try:
        with tempfile.TemporaryDirectory(prefix="ai-compiler-run-") as temp:
            work_dir = Path(temp)
            run_environment = None
            if language == "python":
                interpreter = sys.executable
                if not interpreter or not Path(interpreter).is_file():
                    raise ToolUnavailableError(
                        "The Python interpreter running this backend was not found."
                    )

                source_file = work_dir / "program.py"
                source_file.write_text(code, encoding="utf-8")
                run_command = [interpreter, str(source_file)]
                run_environment = execution_environment(language, interpreter)
            elif language in {"c", "cpp"}:
                source_file = work_dir / (
                    "program.c" if language == "c" else "program.cpp"
                )
                source_file.write_text(code, encoding="utf-8")
                executable = work_dir / (
                    "program.exe" if os.name == "nt" else "program"
                )
                compile_result = compile_native(language, source_file, executable)
                if compile_result.returncode != 0:
                    compilation, diagnostics = failed_compilation(
                        language,
                        compile_result.returncode,
                        compile_result.stdout,
                        compile_result.stderr,
                        source_file,
                    )
                    return jsonify({
                        "success": False,
                        "output": "",
                        "error": compile_result.stderr.strip()
                            or compile_result.stdout.strip()
                            or compilation["message"],
                        "message": compilation["message"],
                        "errorType": "compilation",
                        "returnCode": compile_result.returncode,
                        "stdout": compile_result.stdout,
                        "stderr": compile_result.stderr,
                        "errorDetection": diagnostics,
                        "compilation": compilation,
                    })
                run_command = [str(executable)]
                compiler_name = "gcc" if language == "c" else "g++"
                compiler_candidates = (
                    GCC_CANDIDATES if language == "c" else GXX_CANDIDATES
                )
                compiler = find_tool(compiler_name, compiler_candidates)
                run_environment = execution_environment(language, compiler)
            else:
                result, run_command = compile_java(code, work_dir)
                if result.returncode != 0:
                    compilation, diagnostics = failed_compilation(
                        language,
                        result.returncode,
                        result.stdout,
                        result.stderr,
                        work_dir / f"{java_class_name(code)}.java",
                    )
                    return jsonify({
                        "success": False,
                        "output": "",
                        "error": result.stderr.strip()
                            or result.stdout.strip()
                            or compilation["message"],
                        "message": compilation["message"],
                        "errorType": "compilation",
                        "returnCode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "errorDetection": diagnostics,
                        "compilation": compilation,
                    })
                run_environment = execution_environment(language, run_command[0])

            result = subprocess.run(
                run_command,
                cwd=str(work_dir),
                input=user_input,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=PROCESS_TIMEOUT_SECONDS,
                env=run_environment,
            )
            succeeded = result.returncode == 0
            error = result.stderr.strip() if not succeeded else ""
            message = (
                "Program executed successfully."
                if succeeded
                else f"Program exited with code {result.returncode}."
            )
            return jsonify({
                "success": succeeded,
                "output": result.stdout,
                "error": error,
                "message": message,
                "errorType": None if succeeded else "runtime",
                "returnCode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "compilation": {
                    "success": True,
                    "language": language,
                    "message": f"{language.upper()} compilation succeeded.",
                },
            })
    except ToolUnavailableError as error:
        app.logger.warning("Execution tool unavailable: %s", error)
        return jsonify({
            "success": False,
            "output": "",
            "error": str(error),
            "message": str(error),
            "errorType": "tool unavailable",
            "returnCode": None,
            "stdout": "",
            "stderr": str(error),
            "compilation": {
                "success": False,
                "language": language,
                "message": str(error),
            },
        }), 503
    except subprocess.TimeoutExpired as error:
        app.logger.warning("%s execution timed out", language)
        stdout = as_text(error.stdout)
        stderr = as_text(error.stderr)
        message = f"Program execution timed out after {PROCESS_TIMEOUT_SECONDS} seconds."
        return jsonify({
            "success": False,
            "output": stdout,
            "error": stderr or message,
            "message": message,
            "errorType": "timeout",
            "returnCode": None,
            "stdout": stdout,
            "stderr": stderr,
        }), 408
    except OSError:
        app.logger.exception("Code execution failed")
        message = "An operating-system error prevented program execution."
        return jsonify({
            "success": False,
            "output": "",
            "error": message,
            "message": message,
            "errorType": "execution",
            "returnCode": None,
            "stdout": "",
            "stderr": message,
        }), 500


@app.route("/fix", methods=["POST"])
def fix():
    data, error_response = request_data()
    if error_response:
        return error_response

    code = data["code"]
    language = data["language"]
    try:
        fixed_code = fix_code(code, language)
        if (
            not isinstance(fixed_code, str)
            or not fixed_code.strip()
            or fixed_code.strip() == code.strip()
        ):
            return jsonify({
                "success": False,
                "fixedCode": code,
                "message": (
                    "No valid correction was produced. The original code "
                    "was left unchanged."
                ),
                "error": "No valid correction was produced.",
            }), 422

        validate_correction(fixed_code, language)
        return jsonify({
            "success": True,
            "fixedCode": fixed_code,
            "message": "A code correction was produced.",
            "error": "",
        })
    except ValueError as error:
        return jsonify({
            "success": False,
            "fixedCode": code,
            "message": (
                "The proposed correction did not pass the language syntax "
                f"check: {error}"
            ),
            "error": str(error),
        }), 422
    except Exception as error:
        app.logger.exception("Code correction failed")
        return jsonify({
            "success": False,
            "fixedCode": code,
            "message": f"Code correction failed: {error}",
            "error": str(error),
        }), 502


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False, port=5000)
