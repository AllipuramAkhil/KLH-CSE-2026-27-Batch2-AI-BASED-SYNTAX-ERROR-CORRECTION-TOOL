import { motion, AnimatePresence } from 'framer-motion'

const ErrorPanel = ({ errors = [] }) => {
  return (
    <AnimatePresence>
      {errors.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="bg-red-950/40 border border-red-500/30 rounded-xl p-5"
        >
          <div className="flex items-center mb-4">
            <span className="text-red-400 text-xl mr-2">❌</span>
            <h2 className="text-xl font-bold text-red-400">
              Errors Detected
            </h2>
          </div>

          <div className="space-y-3">
            {errors.map((error, index) => (
              <div
                key={index}
                className="bg-red-900/20 border border-red-500/20 rounded-lg p-3"
              >
                <p className="text-red-300 font-medium">
                  {error.message}
                </p>

                {(error.file || error.line || error.column) && (
                  <p className="text-red-400 text-sm mt-1">
                    {error.file && <span>{error.file} </span>}
                    {error.line && <span>Line: {error.line} </span>}
                    {error.column && <span>Column: {error.column}</span>}
                  </p>
                )}

                <p className="text-gray-400 text-xs mt-1">
                  Type: {error.type}
                </p>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default ErrorPanel
