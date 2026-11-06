import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const WorkflowDrawer = ({
  isOpen,
  onClose,
  analysisData,
  onApplyAIFix,
  isFixing = false,
}) => {
  const [expandedSections, setExpandedSections] = useState({
    lexical: true,
    compilation: false,
    parsing: false,
    semantic: false,
    symbolTable: false,
    intermediateCode: false,
    optimization: false,
    codeGeneration: false,
    errorDetection: false,
    aiSuggestion: false
  })
  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  if (!analysisData) return null

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 z-40"
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            className="fixed right-0 top-0 h-full w-full max-w-2xl bg-slate-950 border-l border-slate-700 z-50 overflow-y-auto"
          >
            <div className="sticky top-0 bg-slate-900 border-b border-slate-700 p-5">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-cyan-400">
                  Compiler Workflow
                </h2>

                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-white"
                >
                  ✖
                </button>
              </div>
            </div>

            <div className="p-5 space-y-4">

              {/* Lexical Analysis */}
              <div className="border border-slate-700 rounded-lg">
                <button
                  onClick={() => toggleSection('lexical')}
                  className="w-full p-4 text-left flex justify-between"
                >
                  <span>▶ Lexical Analysis</span>
                  <span>
                    {expandedSections.lexical ? '▼' : '▶'}
                  </span>
                </button>

                {expandedSections.lexical && (
                  <div className="p-4 border-t border-slate-700">
                    <p className="text-sm text-gray-400 mb-3">
                      {analysisData.lexicalAnalysis?.message ||
                        'Lexical analysis status unavailable.'}
                    </p>
                    <table className="w-full text-sm">
                      <thead>
                        <tr>
                          <th>Token #</th>
                          <th>Type</th>
                          <th>Value</th>
                        </tr>
                      </thead>

                      <tbody>
                        {analysisData.lexical?.map((token, idx) => (
                          <tr key={idx}>
                            <td>{token.number}</td>
                            <td>{token.type}</td>
                            <td>{token.value}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {analysisData.lexical?.length === 0 && (
                      <p className="text-sm text-gray-400 mt-2">
                        No tokens were produced.
                      </p>
                    )}
                  </div>
                )}
              </div>

              <div className="border border-slate-700 rounded-lg">
                <button
                  onClick={() => toggleSection('compilation')}
                  className="w-full p-4 text-left flex justify-between"
                >
                  <span>▶ Compilation and Target Output</span>
                  <span>
                    {expandedSections.compilation ? '▼' : '▶'}
                  </span>
                </button>

                {expandedSections.compilation && (
                  <div className="p-4 border-t border-slate-700">
                    <p>
                      {analysisData.compilation?.message ||
                        'Compilation status unavailable.'}
                    </p>
                    {analysisData.compilation?.returnCode !== undefined && (
                      <p className="text-sm text-gray-400 mt-2">
                        Compiler exit code: {analysisData.compilation.returnCode}
                      </p>
                    )}
                    <p className="text-sm text-gray-400 mt-2">
                      The project does not implement a separate target-code
                      generator. C, C++, and Java target output comes from the
                      selected external compiler; Python is interpreted.
                    </p>
                  </div>
                )}
              </div>

              {/* Parsing */}
              <div className="border border-slate-700 rounded-lg">
                <button
                  onClick={() => toggleSection('parsing')}
                  className="w-full p-4 text-left flex justify-between"
                >
                  <span>▶ Parsing</span>
                  <span>
                    {expandedSections.parsing ? '▼' : '▶'}
                  </span>
                </button>

                {expandedSections.parsing && (
                  <div className="p-4 border-t border-slate-700">
                    <p>{analysisData.parsing?.message || 'Parsing status unavailable.'}</p>

                    <ul className="list-disc ml-6 mt-2">
                      {analysisData.parsing?.matchedRules?.map((rule, idx) => (
                        <li key={idx}>{rule}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
<div className="border border-slate-700 rounded-lg">
  <button
    onClick={() => toggleSection('semantic')}
    className="w-full p-4 text-left flex justify-between"
  >
    <span>▶ Semantic Analysis</span>
    <span>{expandedSections.semantic ? '▼' : '▶'}</span>
  </button>

  {expandedSections.semantic && (
    <div className="p-4 border-t border-slate-700">
      <pre>
        {analysisData.semantic?.result}
      </pre>
    </div>
  )}
</div>
<div className="border border-slate-700 rounded-lg">
  <button
    onClick={() => toggleSection('symbolTable')}
    className="w-full p-4 text-left flex justify-between"
  >
    <span>▶ Symbol Table</span>
    <span>{expandedSections.symbolTable ? '▼' : '▶'}</span>
  </button>

  {expandedSections.symbolTable && (
    <div className="p-4 border-t border-slate-700">
      <pre>
        {analysisData.symbolTable?.join('\n')}
      </pre>
    </div>
  )}
</div>
<div className="border border-slate-700 rounded-lg">
  <button
    onClick={() => toggleSection('intermediateCode')}
    className="w-full p-4 text-left flex justify-between"
  >
    <span>▶ Intermediate Code</span>
    <span>{expandedSections.intermediateCode ? '▼' : '▶'}</span>
  </button>

  {expandedSections.intermediateCode && (
    <div className="p-4 border-t border-slate-700">
      <pre>
        {analysisData.intermediateCode?.join('\n')}
      </pre>
    </div>
  )}
</div>
<div className="border border-slate-700 rounded-lg">
  <button
    onClick={() => toggleSection('optimization')}
    className="w-full p-4 text-left flex justify-between"
  >
    <span>▶ Optimization</span>
    <span>{expandedSections.optimization ? '▼' : '▶'}</span>
  </button>

  {expandedSections.optimization && (
    <div className="p-4 border-t border-slate-700">
      <pre>
        {analysisData.optimization?.join('\n')}
      </pre>
    </div>
  )}
</div>
<div className="border border-slate-700 rounded-lg">
  <button
    onClick={() => toggleSection('codeGeneration')}
    className="w-full p-4 text-left flex justify-between"
  >
    <span>▶ Code Generation</span>
    <span>{expandedSections.codeGeneration ? '▼' : '▶'}</span>
  </button>

  {expandedSections.codeGeneration && (
    <div className="p-4 border-t border-slate-700">
      <pre>
        {analysisData.codeGeneration?.join('\n')}
      </pre>
    </div>
  )}
</div>

              {/* Error Detection */}
              <div className="border border-slate-700 rounded-lg">
                <button
                  onClick={() => toggleSection('errorDetection')}
                  className="w-full p-4 text-left flex justify-between"
                >
                  <span>▶ Error Detection</span>
                  <span>
                    {expandedSections.errorDetection ? '▼' : '▶'}
                  </span>
                </button>

                {expandedSections.errorDetection && (
                  <div className="p-4 border-t border-slate-700">
{analysisData.errorDetection?.map((err, idx) => (
  <div
    key={idx}
    className="mb-3 bg-red-950/30 border border-red-500/30 p-3 rounded"
  >
    <p className="text-red-400 font-bold">
      {err.type}
    </p>

    <p className="text-gray-300">
      Line: {err.line}
    </p>

    <p className="text-gray-300">
      Column: {err.column}
    </p>

    <p className="text-red-300 mt-2">
      {err.message}
    </p>
  </div>
))}                 
 </div>
                )}
              </div>

              {/* AI Suggestion */}
              <div className="border border-slate-700 rounded-lg">
                <button
                  onClick={() => toggleSection('aiSuggestion')}
                  className="w-full p-4 text-left flex justify-between"
                >
                  <span>▶ AI Suggestion</span>
                  <span>
                    {expandedSections.aiSuggestion ? '▼' : '▶'}
                  </span>
                </button>

                {expandedSections.aiSuggestion && (
                  <div className="p-4 border-t border-slate-700">
                    <p>
                      {analysisData.aiSuggestion?.correction}
                    </p>

                    <button
                      onClick={onApplyAIFix}
                      disabled={isFixing}
                      className="mt-4 px-4 py-2 bg-green-600 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg"
                    >
                      {isFixing ? 'Applying Fix...' : 'Apply AI Fix'}
                    </button>
                  </div>
                )}
              </div>

            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default WorkflowDrawer
