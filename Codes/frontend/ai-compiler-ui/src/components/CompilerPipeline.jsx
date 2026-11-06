import React from 'react'

const CompilerPipeline = ({ currentStage }) => {

  const stages = [
    'Lexical Analysis',
    'Parsing',
    'Semantic Analysis',
    'Symbol Table',
    'Intermediate Code',
    'Optimization',
    'Code Generation'
  ]

  return (
    <div className="bg-gray-900 border border-cyan-500/30 rounded-xl p-5">

      <h2 className="text-cyan-400 font-bold text-lg mb-4">
        Compiler Pipeline
      </h2>

      <div className="space-y-3">

        {stages.map((stage, index) => (

          <div
            key={index}
            className={`
              p-3 rounded-lg border
              ${
                index < currentStage
                  ? 'bg-green-900/20 border-green-500 text-green-400'
                  : index === currentStage
                  ? 'bg-cyan-900/20 border-cyan-500 text-cyan-400'
                  : 'bg-gray-800 border-gray-700 text-gray-500'
              }
            `}
          >
            {
              index < currentStage
                ? '✓ '
                : index === currentStage
                ? '▶ '
                : '○ '
            }

            {stage}

          </div>

        ))}

      </div>

    </div>
  )
}

export default CompilerPipeline
