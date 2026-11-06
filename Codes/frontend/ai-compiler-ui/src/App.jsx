import { useRef, useState } from 'react'
import { AnimatePresence } from 'framer-motion'

import Navbar from './components/Navbar'
import LanguageSelector from './components/LanguageSelector'
import CodeEditor from './components/CodeEditor'
import AnalyzeButton from './components/AnalyzeButton'
import RunButton from './components/RunButton'
import ErrorPanel from './components/ErrorPanel'
import SuggestionPanel from './components/SuggestionPanel'
import CompilerWorkflow from './components/CompilerWorkflow'
import WorkflowDrawer from './components/WorkflowDrawer'
import ProgramIOPanel from './components/ProgramIOPanel'

const readApiResponse = async (response) => {
  let data
  try {
    data = await response.json()
  } catch {
    throw new Error(`Backend returned an unreadable response (HTTP ${response.status}).`)
  }

  if (!response.ok && !data.message) {
    throw new Error(`Backend request failed (HTTP ${response.status}).`)
  }

  return data
}

const App = () => {

  const [language, setLanguage] = useState('c')
  const [code, setCode] = useState('')

  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isFixing, setIsFixing] = useState(false)
  const [isRunning, setIsRunning] = useState(false)

  const [output, setOutput] = useState('')
  const [executionError, setExecutionError] = useState('')
  const [executionErrorType, setExecutionErrorType] = useState('')
  const [programInput, setProgramInput] = useState('')
  const [needsInput, setNeedsInput] = useState(false)

  const [errors, setErrors] = useState([])
  const [suggestions, setSuggestions] = useState([])

  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [analysisData, setAnalysisData] = useState(null)
  const analyzeRequestRef = useRef(0)
  const runRequestRef = useRef(0)
  const fixRequestRef = useRef(0)

  const clearResults = () => {
    analyzeRequestRef.current += 1
    runRequestRef.current += 1
    fixRequestRef.current += 1
    setIsAnalyzing(false)
    setIsRunning(false)
    setIsFixing(false)
    setOutput('')
    setExecutionError('')
    setExecutionErrorType('')
    setErrors([])
    setSuggestions([])
    setAnalysisData(null)
    setNeedsInput(false)
  }

  const handleCodeChange = (nextCode) => {
    setCode(nextCode)
    clearResults()
  }

  const handleLanguageChange = (nextLanguage) => {
    setLanguage(nextLanguage)
    clearResults()
  }

  const handleAnalyze = async () => {
    const requestId = ++analyzeRequestRef.current
    runRequestRef.current += 1
    fixRequestRef.current += 1
    setIsRunning(false)
    setIsFixing(false)
    setIsAnalyzing(true)
    setAnalysisData(null)
    setErrors([])
    setSuggestions([])
    try {
      const response = await fetch(
        'http://127.0.0.1:5000/analyze',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code,
            language,
          }),
        }
      )
      const data = await readApiResponse(response)
      if (requestId !== analyzeRequestRef.current) return
      setAnalysisData(data)
      const diagnostics = Array.isArray(data.errorDetection)
        ? data.errorDetection
        : []
      setErrors(diagnostics)

      if (diagnostics.length > 0) {
        const firstError = diagnostics[0]
        setSuggestions([
          {
            message: firstError.line
              ? `Compiler diagnostic at line ${firstError.line}`
              : 'Compiler diagnostic',
            fix: firstError.message,
            confidence: 0,
          },
        ])
      } else {
        setSuggestions([
          {
            message: data.success
              ? 'Code Analysis'
              : 'Analysis did not complete',
            fix: data.message || 'No compiler diagnostics were returned.',
            confidence: data.success ? 100 : 0,
          },
        ])
      }
    } catch (error) {
      if (requestId !== analyzeRequestRef.current) return
      console.error('Backend Error:', error)
      setErrors([{
        type: 'Backend Error',
        line: null,
        message: error.message || 'Failed to analyze code.',
      }])
    } finally {
      if (requestId === analyzeRequestRef.current) {
        setIsAnalyzing(false)
      }
    }
  }

  const handleApplyFix = async () => {
    const requestId = ++fixRequestRef.current
    analyzeRequestRef.current += 1
    runRequestRef.current += 1
    setIsAnalyzing(false)
    setIsRunning(false)
    const originalCode = code
    try {
      setIsFixing(true)
      const response = await fetch(
        'http://127.0.0.1:5000/fix',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code,
            language,
          }),
        }
      )
      const data = await readApiResponse(response)
      if (requestId !== fixRequestRef.current) return
      if (
        data.success === true &&
        typeof data.fixedCode === 'string' &&
        data.fixedCode.trim() &&
        data.fixedCode.trim() !== originalCode.trim()
      ) {
        analyzeRequestRef.current += 1
        runRequestRef.current += 1
        setIsAnalyzing(false)
        setIsRunning(false)
        setCode(data.fixedCode)
        setErrors([])
        setOutput('')
        setExecutionError('')
        setExecutionErrorType('')
        setNeedsInput(false)
        setAnalysisData(null)
        setSuggestions([
          {
            message: 'AI Fix Applied',
            fix: data.message || 'A correction was applied to the editor.',
            confidence: 100,
          },
        ])
      } else {
        setSuggestions([{
          message: 'No fix was applied',
          fix: data.message || 'No valid correction was produced.',
          confidence: 0,
        }])
      }
    } catch (error) {
      if (requestId !== fixRequestRef.current) return
      console.error('AI Fix Error:', error)
      setSuggestions([{
        message: 'Code correction failed',
        fix: error.message || 'The correction service could not be reached.',
        confidence: 0,
      }])
    } finally {
      if (requestId === fixRequestRef.current) {
        setIsFixing(false)
      }
    }
  }

  const handleRun = async () => {
    const requestId = ++runRequestRef.current
    analyzeRequestRef.current += 1
    fixRequestRef.current += 1
    setIsAnalyzing(false)
    setIsFixing(false)
    const inputPattern = {
      c: /\b(?:scanf|gets|fgets)\s*\(/,
      cpp: /\b(?:cin|getline)\s*(?:>>|\()/,
      java: /\b(?:next\w*|readLine)\s*\(/,
      python: /\binput\s*\(/,
    }[language]
    setNeedsInput(inputPattern.test(code))
    setOutput('')
    setExecutionError('')
    setExecutionErrorType('')
    setErrors([])
    setSuggestions([])
    setAnalysisData(null)
    setIsRunning(true)
    try {
      const response = await fetch(
        'http://127.0.0.1:5000/run',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code,
            language,
            input: programInput,
          }),
        }
      )
      const data = await readApiResponse(response)
      if (requestId !== runRequestRef.current) return
      setOutput(typeof data.output === 'string' ? data.output : '')
      setExecutionError(
        data.error ||
        (!data.success ? data.message : '') ||
        ''
      )
      setExecutionErrorType(data.errorType || '')
    } catch (error) {
      if (requestId !== runRequestRef.current) return
      console.error(error)
      setExecutionError(error.message || 'Failed to connect to backend.')
      setExecutionErrorType('backend')
    } finally {
      if (requestId === runRequestRef.current) {
        setIsRunning(false)
      }
    }
  }

  return (

    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-black">

      <Navbar />

      <main className="container mx-auto px-6 py-8">

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          <div className="lg:col-span-2 space-y-6">

            <div className="glass-card p-1">

              <div className="bg-gray-950/50 rounded-lg p-4">

                <LanguageSelector
                  selectedLanguage={language}
                  onLanguageChange={handleLanguageChange}
                />

              </div>

            </div>

            <div className="glass-card overflow-hidden">

              <div className="border-b border-gray-700/50 px-4 py-3">

                <h3 className="text-gray-300 font-semibold text-sm">
                  Code Editor
                </h3>

              </div>

              <CodeEditor
                language={language}
                value={code}
                onChange={handleCodeChange}
              />

            </div>

            <div className="flex gap-4 flex-wrap">

              <AnalyzeButton
                onClick={handleAnalyze}
                isLoading={isAnalyzing}
              />

              <RunButton
                onClick={handleRun}
                isRunning={isRunning}
              />

              <CompilerWorkflow
                onClick={() =>
                  setIsDrawerOpen(true)
                }
              />

            </div>

            <ProgramIOPanel
              needsInput={needsInput}
              programInput={programInput}
              setProgramInput={setProgramInput}
              output={output}
              error={executionError}
              errorType={executionErrorType}
              isRunning={isRunning}
            />

          </div>

          <div className="space-y-6">

            <AnimatePresence mode="wait">

              {errors.length > 0 && (
                <ErrorPanel errors={errors} />
              )}

            </AnimatePresence>

            <AnimatePresence mode="wait">

              {suggestions.length > 0 && (
                <SuggestionPanel
                  suggestions={suggestions}
                  onApplyFix={handleApplyFix}
                  isFixing={isFixing}
                />
              )}

            </AnimatePresence>

          </div>

        </div>

      </main>

      <WorkflowDrawer
        isOpen={isDrawerOpen}
        onClose={() =>
          setIsDrawerOpen(false)
        }
        analysisData={analysisData}
        onApplyAIFix={handleApplyFix}
        isFixing={isFixing}
      />

    </div>
  )
}

export default App
