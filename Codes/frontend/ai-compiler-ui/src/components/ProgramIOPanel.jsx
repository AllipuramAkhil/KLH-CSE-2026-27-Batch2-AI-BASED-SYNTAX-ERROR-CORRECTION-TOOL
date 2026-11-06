const ProgramIOPanel = ({
  needsInput,
  programInput,
  setProgramInput,
  output,
  error,
  errorType,
  isRunning,
}) => {

  return (
    <div className="bg-gray-900 border border-green-500/30 rounded-xl p-5">

      <h2 className="text-green-400 font-bold text-lg mb-4">
        Program I/O
      </h2>

      {needsInput && (
        <div className="mb-4">

          <label className="text-blue-400 text-sm">
            Program Input
          </label>

          <textarea
            value={programInput}
            onChange={(e) =>
              setProgramInput(
                e.target.value
              )
            }
            placeholder="Enter program input here..."
            className="
              w-full
              h-24
              mt-2
              bg-black
              text-white
              border
              border-gray-700
              rounded-lg
              p-3
              outline-none
            "
          />

        </div>
      )}

      <div>

        <label className="text-green-400 text-sm">
          Program Output
        </label>

        <pre
          className="
            mt-2
            bg-black
            text-green-300
            p-3
            rounded-lg
            min-h-[100px]
            whitespace-pre-wrap
          "
        >
          {isRunning ? "Running program..." : output || "No Output"}
        </pre>

      </div>

      {error && (
        <div className="mt-4">
          <label className="text-red-400 text-sm">
            {errorType === 'compilation'
              ? 'Compilation Error'
              : errorType === 'runtime'
                ? 'Runtime Error'
                : 'Execution Error'}
          </label>
          <pre className="mt-2 bg-black text-red-300 p-3 rounded-lg whitespace-pre-wrap overflow-x-auto">
            {error}
          </pre>
        </div>
      )}

    </div>
  )
}

export default ProgramIOPanel
