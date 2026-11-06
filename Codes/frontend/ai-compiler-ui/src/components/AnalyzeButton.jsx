import React from 'react'
import { motion } from 'framer-motion'

const AnalyzeButton = ({ onClick, isLoading }) => {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      disabled={isLoading}
      className={`relative px-8 py-3 rounded-lg font-semibold text-white overflow-hidden group ${
        isLoading
          ? 'bg-gray-600 cursor-not-allowed'
          : 'bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 hover:shadow-2xl hover:shadow-purple-500/50'
      } transition-all duration-300`}
    >
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
        animate={isLoading ? {} : { x: ['-100%', '100%'] }}
        transition={
          isLoading
            ? {}
            : {
                duration: 1.5,
                repeat: Infinity,
                repeatDelay: 0.5,
              }
        }
        style={{ x: '-100%' }}
      />

      <div className="relative flex items-center space-x-2">
        {isLoading ? (
          <>
            <svg
              className="animate-spin h-5 w-5 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>

              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 
                5.291A7.962 7.962 0 014 12H0c0 3.042 
                1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>

            <span>Analyzing Code...</span>
          </>
        ) : (
          <>
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 
                1.636l-.707.707M21 12h-1M4 12H3m3.343
                -5.657l-.707-.707m2.828 9.9a5 5 0 
                117.072 0l-.548.547A3.374 3.374 0 
                0014 18.469V19a2 2 0 11-4 
                0v-.531c0-.895-.356-1.754-.988-2.386
                l-.548-.547z"
              />
            </svg>

            <span>Analyze Code</span>
          </>
        )}
      </div>
    </motion.button>
  )
}

export default AnalyzeButton
