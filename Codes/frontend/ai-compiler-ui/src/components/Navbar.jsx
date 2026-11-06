import React from 'react'
import { motion } from 'framer-motion'
import StatusIndicator from './StatusIndicator'

const Navbar = () => {
  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 100 }}
      className="glass-card sticky top-4 mx-6 z-50 backdrop-blur-xl bg-gray-900/60"
    >
      <div className="flex justify-between items-center px-6 py-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 3v2m6-2v2M9 19v2m6-2v2M5 7h14M5 11h14M5 15h14M5 19h14" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M3 7h18M3 11h18M3 15h18M3 19h18" />
            </svg>
          </div>

          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              AI Compiler Assistant
            </h1>

            <p className="text-xs text-gray-400">
              Intelligent Code Analysis & Optimization
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-6">
          <div className="hidden md:flex items-center space-x-2">
            <span className="text-gray-300 text-sm">
              System Ready
            </span>

            <StatusIndicator status="online" />
          </div>

          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center cursor-pointer hover:scale-110 transition-transform">
              <svg
                className="w-4 h-4 text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            </div>

            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center cursor-pointer hover:scale-110 transition-transform">
              <span className="text-white text-sm font-semibold">
                AI
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.nav>
  )
}

export default Navbar
