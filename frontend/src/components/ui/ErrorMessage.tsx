interface ErrorMessageProps {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}

export default function ErrorMessage({
  title = "Error",
  message,
  onRetry,
  className = ''
}: ErrorMessageProps) {
  return (
    <div className={`bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-red-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800 dark:text-red-300">
            {title}
          </h3>
          <p className="mt-1 text-sm text-red-700 dark:text-red-400">
            {message}
          </p>
          {onRetry && (
            <div className="mt-4">
              <button
                onClick={onRetry}
                className="bg-red-100 dark:bg-red-800/20 hover:bg-red-200 dark:hover:bg-red-800/40 text-red-800 dark:text-red-300 px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}