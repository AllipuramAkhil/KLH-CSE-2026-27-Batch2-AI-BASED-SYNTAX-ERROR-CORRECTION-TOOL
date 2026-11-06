import React from 'react'
import { motion } from 'framer-motion'

const CompilerWorkflow = ({ onClick }) => {
  return (
    <motion.button
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className="px-6 py-3 rounded-xl border border-blue-500/30 bg-blue-950/20 hover:bg-blue-900/30 transition-all text-blue-300 font-medium flex items-center gap-2"
    >
      <span>📊</span>
      <span>Show Compiler Workflow</span>
    </motion.button>
  )
}

export default CompilerWorkflow
