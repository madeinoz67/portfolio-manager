interface ErrorMessageProps {
  message: string
  className?: string
}

export default function ErrorMessage({ message, className = '' }: ErrorMessageProps) {
  return (
    <div className={`bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-200 px-4 py-3 rounded animate-fade-in ${className}`}>
      {message}
    </div>
  )
}