import React from 'react'

const InputPanel = ({
  input,
  setInput,
}) => {
  return (
    <div className="bg-gray-900 border border-blue-500/30 rounded-xl p-5">
      <h2 className="text-blue-400 font-bold text-lg mb-3">
        Program Input
      </h2>

      <textarea
        value={input}
        onChange={(e) =>
          setInput(e.target.value)
        }
        placeholder="Enter input here..."
        className="
          w-full
          h-28
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
  )
}

export default InputPanel
