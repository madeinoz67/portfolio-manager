export default function PortfolioCardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border dark:border-gray-700 animate-pulse">
      {/* Title skeleton */}
      <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-2 w-3/4"></div>
      
      {/* Description skeleton */}
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-4 w-full"></div>
      
      <div className="space-y-2">
        {/* Total Value skeleton */}
        <div className="flex justify-between">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16"></div>
        </div>
        
        {/* Daily Change skeleton */}
        <div className="flex justify-between">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
        </div>
        
        {/* Created date skeleton */}
        <div className="pt-2">
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
        </div>
      </div>
      
      {/* Button skeletons */}
      <div className="mt-4 flex space-x-2">
        <div className="flex-1 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div className="flex-1 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    </div>
  )
}

export function PortfolioGridSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: 6 }).map((_, index) => (
        <PortfolioCardSkeleton key={index} />
      ))}
    </div>
  )
}