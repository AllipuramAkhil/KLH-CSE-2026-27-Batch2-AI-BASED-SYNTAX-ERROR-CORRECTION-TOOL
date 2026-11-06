import React from 'react'
import { motion } from 'framer-motion'

const languages = [
  { id: 'c', name: 'C', icon: '⚙️' },
  { id: 'cpp', name: 'C++', icon: '⚡' },
  { id: 'java', name: 'Java', icon: '☕' },
  { id: 'python', name: 'Python', icon: '🐍' }
]

const LanguageSelector = ({ selectedLanguage, onLanguageChange }) => {
  return (
    <div className="flex space-x-3">
      {languages.map((lang) => (
        <motion.button
          key={lang.id}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onLanguageChange(lang.id)}
          className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 flex items-center space-x-2 ${
            selectedLanguage === lang.id
              ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/30'
              : 'bg-gray-800/50 text-gray-300 hover:bg-gray-700/50 border border-gray-700/50'
          }`}
        >
          <span className="text-lg">{lang.icon}</span>
          <span>{lang.name}</span>
        </motion.button>
      ))}
    </div>
  )
}

export default LanguageSelector

