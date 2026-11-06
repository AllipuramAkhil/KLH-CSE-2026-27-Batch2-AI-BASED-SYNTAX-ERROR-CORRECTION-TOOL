import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as backend


client = backend.app.test_client()

VALID_C = """#include <stdio.h>
int main(void) {
    printf("Hello C!\\n");
    return 0;
}
"""
INVALID_C = """#include <stdio.h>
int main(void) {
    printf("Hello C!")
    return 0;
}
"""


class CompilerApiTests(unittest.TestCase):
    def post(self, endpoint, code, language, **extra):
        return client.post(
            endpoint,
            json={"code": code, "language": language, **extra},
        )

    def test_health_reports_detected_tools_and_cors(self):
        response = client.get(
            "/",
            headers={"Origin": "http://localhost:5174"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["success"])
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"],
            "http://localhost:5174",
        )
        self.assertIsNotNone(response.json["tools"]["python"])

        rejected_origin = client.get(
            "/",
            headers={"Origin": "http://untrusted.invalid"},
        )
        self.assertNotIn(
            "Access-Control-Allow-Origin",
            rejected_origin.headers,
        )

    def test_empty_source_is_rejected(self):
        for endpoint in ("/analyze", "/run", "/fix"):
            with self.subTest(endpoint=endpoint):
                response = client.post(endpoint, json={"code": "  "})
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.json["success"])

    def test_oversized_request_has_json_error(self):
        response = client.post(
            "/run",
            json={"code": "x" * (1024 * 1024 + 1), "language": "python"},
        )
        self.assertEqual(response.status_code, 413)
        self.assertIn("1 MiB", response.json["message"])

    def test_lexer_handles_comments_directives_tokens_and_operators(self):
        source = """#include <stdio.h>
#define FACTOR 4
int main(void) {
    // comment words should not become tokens
    /* block comment with a fake number 900 */
    int value = 10;
    value += FACTOR;
    printf("value=%d\\n", value);
    return 0;
}
"""
        result = self.post("/analyze", source, "c")
        self.assertEqual(result.status_code, 200)
        data = result.json
        self.assertTrue(data["lexicalAnalysis"]["success"])
        token_pairs = [(token["type"], token["value"]) for token in data["lexical"]]
        self.assertIn(("PREPROCESSOR", "#include"), token_pairs)
        self.assertIn(("PREPROCESSOR", "#define"), token_pairs)
        self.assertIn(("KEYWORD", "int"), token_pairs)
        self.assertIn(("IDENTIFIER", "value"), token_pairs)
        self.assertIn(("NUMBER", "10"), token_pairs)
        self.assertIn(("OPERATOR", "+="), token_pairs)
        self.assertIn(("STRING", '"value=%d\\n"'), token_pairs)
        self.assertFalse(any("comment" in value for _, value in token_pairs))
        self.assertFalse(any(value == "900" for _, value in token_pairs))

    @unittest.skipUnless(
        backend.find_tool("gcc", backend.GCC_CANDIDATES),
        "GCC is unavailable",
    )
    def test_c_compiles_runs_reports_diagnostic_and_handles_repeated_runs(self):
        good = self.post("/run", VALID_C, "c")
        self.assertTrue(good.json["success"], good.json)
        self.assertEqual(good.json["output"], "Hello C!\n")

        bad_analysis = self.post("/analyze", INVALID_C, "c")
        self.assertFalse(bad_analysis.json["compilation"]["success"])
        diagnostic = bad_analysis.json["errorDetection"][0]
        self.assertIn("source.c", diagnostic["file"])
        self.assertIsInstance(diagnostic["line"], int)
        self.assertIsInstance(diagnostic["column"], int)
        self.assertIn("expected", diagnostic["message"])

        bad_run = self.post("/run", INVALID_C, "c")
        self.assertFalse(bad_run.json["success"])
        self.assertEqual(bad_run.json["errorType"], "compilation")

        runtime_error = self.post(
            "/run",
            "int main(void) { return 7; }",
            "c",
        )
        self.assertFalse(runtime_error.json["success"])
        self.assertEqual(runtime_error.json["errorType"], "runtime")
        self.assertEqual(runtime_error.json["returnCode"], 7)

        repeated = self.post("/run", VALID_C, "c")
        self.assertTrue(repeated.json["success"])
        self.assertEqual(repeated.json["output"], "Hello C!\n")

    @unittest.skipUnless(
        backend.find_tool("g++", backend.GXX_CANDIDATES),
        "G++ is unavailable",
    )
    def test_cpp_compiles_runs_and_reports_syntax_errors(self):
        source = """#include <iostream>
int main() {
    std::cout << "Hello C++!" << std::endl;
    return 0;
}
"""
        result = self.post("/run", source, "cpp")
        self.assertTrue(result.json["success"], result.json)
        self.assertEqual(result.json["output"], "Hello C++!\n")

        invalid = self.post(
            "/analyze",
            "int main() { return 0 }",
            "cpp",
        )
        self.assertFalse(invalid.json["compilation"]["success"])
        self.assertTrue(invalid.json["errorDetection"])

        runtime_error = self.post(
            "/run",
            "int main() { return 5; }",
            "cpp",
        )
        self.assertFalse(runtime_error.json["success"])
        self.assertEqual(runtime_error.json["errorType"], "runtime")
        self.assertEqual(runtime_error.json["returnCode"], 5)

    @unittest.skipUnless(
        backend.find_tool("java") and backend.find_tool("javac"),
        "A Java JDK is unavailable",
    )
    def test_java_compiles_runs_and_reports_syntax_errors(self):
        source = """public class Main {
    public static void main(String[] args) {
        System.out.println("Hello Java!");
    }
}
"""
        result = self.post("/run", source, "java")
        self.assertTrue(result.json["success"], result.json)
        self.assertEqual(result.json["output"], "Hello Java!\n")

        invalid = self.post(
            "/analyze",
            'public class Main { public static void main(String[] args) { System.out.println("x") } }',
            "java",
        )
        self.assertFalse(invalid.json["compilation"]["success"])
        diagnostic = invalid.json["errorDetection"][0]
        self.assertTrue(diagnostic["file"].endswith("Main.java"))
        self.assertIsInstance(diagnostic["line"], int)
        self.assertIsInstance(diagnostic["column"], int)

        runtime_error = self.post(
            "/run",
            """public class Main {
    public static void main(String[] args) {
        throw new IllegalStateException("runtime failure");
    }
}
""",
            "java",
        )
        self.assertFalse(runtime_error.json["success"])
        self.assertEqual(runtime_error.json["errorType"], "runtime")
        self.assertIn("IllegalStateException", runtime_error.json["error"])

    def test_python_runs_and_reports_syntax_and_runtime_errors(self):
        result = self.post("/run", 'print("Hello Python!")', "python")
        self.assertTrue(result.json["success"], result.json)
        self.assertEqual(result.json["output"], "Hello Python!\n")

        runtime_error = self.post(
            "/run",
            "print(unknown_variable)",
            "python",
        )
        self.assertFalse(runtime_error.json["success"])
        self.assertEqual(runtime_error.json["errorType"], "runtime")
        self.assertIn("NameError", runtime_error.json["error"])

        syntax_error = self.post(
            "/analyze",
            'print("unterminated)',
            "python",
        )
        self.assertFalse(syntax_error.json["compilation"]["success"])
        self.assertEqual(syntax_error.json["errorDetection"][0]["line"], 1)

    def test_runtime_exit_codes_and_temp_directory_cleanup(self):
        temp_root = Path(tempfile.gettempdir())
        before = set(temp_root.glob("ai-compiler-run-*"))
        result = self.post("/run", "raise SystemExit(7)", "python")
        after = set(temp_root.glob("ai-compiler-run-*"))

        self.assertFalse(result.json["success"])
        self.assertEqual(result.json["errorType"], "runtime")
        self.assertEqual(result.json["returnCode"], 7)
        self.assertEqual(before, after)

    def test_timeout_returns_clear_error(self):
        with patch.object(backend, "PROCESS_TIMEOUT_SECONDS", 0.1):
            result = self.post("/run", "while True: pass", "python")

        self.assertEqual(result.status_code, 408)
        self.assertEqual(result.json["errorType"], "timeout")
        self.assertIn("timed out", result.json["message"])

    def test_missing_native_compiler_returns_clear_unavailable_error(self):
        with patch.object(backend, "find_tool", return_value=None):
            result = self.post("/run", VALID_C, "c")

        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.json["errorType"], "tool unavailable")
        self.assertIn("GCC was not found", result.json["error"])

    @unittest.skipUnless(
        backend.find_tool("gcc", backend.GCC_CANDIDATES),
        "GCC is unavailable",
    )
    def test_local_fix_is_validated_and_failed_fix_preserves_original(self):
        source = """#include <stdio.h>
int main(void) {
    printf("fixed") /* preserve this block comment */ // preserve this line comment
    return 0;
}
"""
        fixed = client.post("/fix", json={"code": source, "language": "c"})
        self.assertEqual(fixed.status_code, 200, fixed.json)
        self.assertTrue(fixed.json["success"])
        self.assertNotEqual(fixed.json["fixedCode"], source)
        self.assertIn("/* preserve this block comment */", fixed.json["fixedCode"])
        self.assertIn("// preserve this line comment", fixed.json["fixedCode"])
        compiled = self.post("/analyze", fixed.json["fixedCode"], "c")
        self.assertTrue(compiled.json["compilation"]["success"])

        original = "int main(void) { return 0; }"
        with patch.object(backend, "fix_code", return_value="not valid C"):
            rejected = client.post(
                "/fix",
                json={"code": original, "language": "c"},
            )
        self.assertEqual(rejected.status_code, 422)
        self.assertFalse(rejected.json["success"])
        self.assertEqual(rejected.json["fixedCode"], original)


if __name__ == "__main__":
    unittest.main()
