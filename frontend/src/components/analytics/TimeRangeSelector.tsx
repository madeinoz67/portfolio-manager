interface TimeRangeSelectorProps {
  selected: string
  onSelect: (range: string) => void
}

const timeRanges = [
  { label: '1D', value: '1D' },
  { label: '1W', value: '1W' },
  { label: '1M', value: '1M' },
  { label: '3M', value: '3M' },
  { label: '1Y', value: '1Y' },
  { label: 'ALL', value: 'ALL' }
]

export default function TimeRangeSelector({ selected, onSelect }: TimeRangeSelectorProps) {
  return (
    <div className="flex items-center space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
      {timeRanges.map((range) => (
        <button
          key={range.value}
          onClick={() => onSelect(range.value)}
          className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
            selected === range.value
              ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          {range.label}
        </button>
      ))}
    </div>
  )
}