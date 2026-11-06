# AI Compiler Assistant

React/Vite frontend with a Flask API for C, C++, Java, and Python program
analysis and execution. This is a local educational tool, **not a sandbox**:
submitted programs execute as the current Windows user and can access files,
environment variables, and operating-system facilities available to that user.
Keep the backend bound to loopback and do not expose port 5000 to a network.

## Requirements

- Windows 10/11
- Python 3.10 or newer
- Node.js 22 and npm
- MSYS2 UCRT64 GCC/G++ (`C:\msys64\ucrt64\bin\gcc.exe` and `g++.exe`)
- MSYS2 Flex (`C:\msys64\usr\bin\flex.exe`) to regenerate the lexer
- A JDK with both `java` and `javac` on `PATH` or under `JAVA_HOME`

Install the MSYS2 compiler and Flex packages from an MSYS2 UCRT64 terminal:

```bash
pacman -S --needed mingw-w64-ucrt-x86_64-gcc flex
```

Install a JDK separately if Java is unavailable. The backend reports detected
tool paths from `GET /`; Java execution returns a clear unavailable-runtime
error if either `java` or `javac` cannot be found.

## Setup

In PowerShell:

```powershell
Set-Location 'D:\CD_PROJECT\backend\flask_api'
python -m pip install -r requirements.txt
```

An Ollama Python package and local model are optional. C/C++ have a deterministic
local fixer for common missing-semicolon errors; other corrections may require
the optional Ollama service. Configure a different model with `OLLAMA_MODEL`.
The backend reports AI service errors and preserves the original source when a
correction is unavailable or fails validation.

Install the frontend dependencies once:

```powershell
Set-Location 'D:\CD_PROJECT\frontend\ai-compiler-ui'
npm ci
```

## Start the application

Open two PowerShell terminals.

Terminal 1 — backend:

```powershell
Set-Location 'D:\CD_PROJECT\backend\flask_api'
$env:Path = "C:\msys64\ucrt64\bin;C:\msys64\usr\bin;$env:Path"
python app.py
```

Terminal 2 — frontend:

```powershell
Set-Location 'D:\CD_PROJECT\frontend\ai-compiler-ui'
npm run dev -- --host 127.0.0.1 --port 5174
```

Open <http://localhost:5174>. The API listens on
<http://127.0.0.1:5000>; CORS allows the two local frontend origins on port
5174.

## Lexer

The Flex source is `lexer/lexer.l`. The lexer reads `input.c` from its current
working directory, so the API creates that file in an isolated temporary
directory and launches `lexer/lexer.exe` there. To rebuild the Windows
executable from the project root:

```powershell
$env:Path = "C:\msys64\ucrt64\bin;C:\msys64\usr\bin;$env:Path"
Set-Location 'D:\CD_PROJECT\lexer'
& 'C:\msys64\usr\bin\flex.exe' -o lex.yy.c lexer.l
& 'C:\msys64\ucrt64\bin\gcc.exe' lex.yy.c -o lexer.exe
```

## Compiler workflow implementation status

- **Lexical analysis:** implemented for C by the Flex lexer. C++, Java, and
  Python currently report lexical analysis as not implemented.
- **Parsing, semantic analysis, symbol-table generation, intermediate-code
  generation, and project-owned optimization:** not implemented. The workflow
  reports these as placeholders; the API does not claim their results.
- **Compilation and target output:** C/C++ use GCC/G++; Java uses `javac` and
  `java`; Python is interpreted with the Python executable running Flask.
  Native/class target generation is performed by those external toolchains,
  not by a separate compiler stage implemented in this project.

## Tests and checks

Run backend API tests (with the compiler/runtime dependencies available):

```powershell
Set-Location 'D:\CD_PROJECT\backend\flask_api'
$env:Path = "C:\msys64\ucrt64\bin;C:\msys64\usr\bin;$env:Path"
python -m unittest -v test_app
```

Run frontend checks:

```powershell
Set-Location 'D:\CD_PROJECT\frontend\ai-compiler-ui'
npm run build
npx eslint src/App.jsx src/components/ProgramIOPanel.jsx src/components/ErrorPanel.jsx src/components/SuggestionPanel.jsx src/components/WorkflowDrawer.jsx
```

## Execution safety

Each subprocess uses argument arrays (not `shell=True`), a temporary working
directory, captured output, and a 15-second timeout. Temporary source and
compiled files are removed when the request finishes. These measures are not
isolation: a submitted program can still read/write accessible files, spawn
processes, or consume resources before timeout cleanup. Only run code you trust.
