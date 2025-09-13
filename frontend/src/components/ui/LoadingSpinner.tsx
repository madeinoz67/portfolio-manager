interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large'
  className?: string
}

const sizeClasses = {
  small: 'h-8 w-8 border-2',
  medium: 'h-16 w-16 border-2', 
  large: 'h-32 w-32 border-2'
}

export default function LoadingSpinner({ size = 'medium', className = '' }: LoadingSpinnerProps) {
  return (
    <div className={`animate-spin rounded-full border-b-blue-600 dark:border-b-blue-400 ${sizeClasses[size]} ${className}`}></div>
  )
}