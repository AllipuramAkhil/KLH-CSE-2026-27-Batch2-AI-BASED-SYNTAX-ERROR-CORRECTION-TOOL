import { motion, AnimatePresence } from 'framer-motion'

const SuggestionPanel = ({
  suggestions = [],
  onApplyFix,
  isFixing = false,
}) => {
  return (
    <AnimatePresence>
      {suggestions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="bg-green-950/40 border border-green-500/30 rounded-xl p-5"
        >
          <div className="flex items-center mb-4">
            <span className="text-green-400 text-xl mr-2">
              💡
            </span>

            <h2 className="text-xl font-bold text-green-400">
              AI Suggestions
            </h2>
          </div>

          <div className="space-y-3">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="bg-green-900/20 border border-green-500/20 rounded-lg p-4"
              >
                <p className="text-green-300 font-medium">
                  {suggestion.message}
                </p>

                <div className="mt-3 bg-black/30 rounded p-3">
                  <code className="text-green-400 text-sm">
                    {suggestion.fix}
                  </code>
                </div>

                <div className="flex justify-between items-center mt-3">
                  <span className="text-xs text-gray-400">
                    Confidence: {suggestion.confidence}%
                  </span>

                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onApplyFix?.(suggestion)}
                    disabled={isFixing}
                    className="px-3 py-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white text-sm"
                  >
                    {isFixing ? 'Fixing...' : 'Apply Fix'}
                  </motion.button>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default SuggestionPanel
