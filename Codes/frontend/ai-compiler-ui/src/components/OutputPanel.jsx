import React from 'react'

const OutputPanel = ({ output }) => {
  return (
    <div className="bg-gray-900 border border-green-500/30 rounded-xl p-5">
      <h2 className="text-green-400 font-bold text-lg mb-3">
        Program Output
      </h2>

      <pre className="text-green-300 whitespace-pre-wrap">
        {output || 'No Output'}
      </pre>
    </div>
  )
}

export default OutputPanel
