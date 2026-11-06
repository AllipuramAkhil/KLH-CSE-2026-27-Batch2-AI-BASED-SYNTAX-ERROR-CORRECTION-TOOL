import React from 'react'
import Editor from '@monaco-editor/react'

const CodeEditor = ({ language, value, onChange }) => {
  const getLanguageId = () => {
    const map = {
      c: 'c',
      cpp: 'cpp',
      java: 'java',
      python: 'python'
    }
    return map[language] || 'c'
  }

  return (
    <div className="h-[500px] w-full overflow-hidden">
      <Editor
        height="100%"
        language={getLanguageId()}
        value={value}
        onChange={onChange}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: 'JetBrains Mono, Fira Code, monospace',
          lineNumbers: 'on',
          renderWhitespace: 'selection',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 4,
          insertSpaces: true,
          bracketPairColorization: { enabled: true },
          guides: { bracketPairs: true },
          wordWrap: 'on',
          padding: { top: 16, bottom: 16 },
          glyphMargin: false,
          folding: true,
          lineDecorationsWidth: 10,
          lineNumbersMinChars: 3,
          renderLineHighlight: 'all',
          smoothScrolling: true,
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
        }}
        loading={
          <div className="flex items-center justify-center h-full bg-gray-900">
            <div className="text-gray-400">
              Loading Editor...
            </div>
          </div>
        }
      />
    </div>
  )
}

export default CodeEditor
