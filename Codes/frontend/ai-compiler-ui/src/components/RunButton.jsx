import React from 'react'
import { motion } from 'framer-motion'

const RunButton = ({ onClick, isRunning }) => {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      disabled={isRunning}
      className={`relative px-8 py-3 rounded-lg font-semibold text-white overflow-hidden ${
        isRunning
          ? 'bg-gray-600 cursor-not-allowed'
          : 'bg-gradient-to-r from-green-500 to-emerald-600'
      }`}
    >
      {isRunning ? (
        <span>Running...</span>
      ) : (
        <span>▶ Run Code</span>
      )}
    </motion.button>
  )
}

export default RunButton
