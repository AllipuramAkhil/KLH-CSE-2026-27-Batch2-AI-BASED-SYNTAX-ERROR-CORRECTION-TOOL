import React from 'react'
import { motion } from 'framer-motion'

const StatusIndicator = ({ status = 'online' }) => {
  const statusConfig = {
    online: {
      color: 'bg-green-500',
      pulse: true,
      text: 'Online'
    },
    offline: {
      color: 'bg-gray-500',
      pulse: false,
      text: 'Offline'
    },
    analyzing: {
      color: 'bg-yellow-500',
      pulse: true,
      text: 'Analyzing'
    }
  }

  const config = statusConfig[status]

  return (
    <div className="flex items-center space-x-2">
      <div className="relative">
        <motion.div
          className={`w-2.5 h-2.5 ${config.color} rounded-full`}
          animate={config.pulse ? {
            scale: [1, 1.2, 1],
            opacity: [1, 0.8, 1]
          } : {}}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        {config.pulse && (
          <motion.div
            className={`absolute inset-0 ${config.color} rounded-full opacity-75`}
            animate={{
              scale: [1, 1.5, 2],
              opacity: [0.75, 0.3, 0]
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeOut"
            }}
          />
        )}
      </div>
      <span className="text-xs text-gray-400 hidden sm:inline">
        {config.text}
      </span>
    </div>
  )
}

export default StatusIndicator
