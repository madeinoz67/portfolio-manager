'use client'

import { forwardRef } from 'react'

interface DatePickerProps {
  id?: string
  name?: string
  value: string
  onChange: (value: string) => void
  min?: string
  max?: string
  required?: boolean
  disabled?: boolean
  className?: string
  placeholder?: string
}

const DatePicker = forwardRef<HTMLInputElement, DatePickerProps>(({
  id,
  name,
  value,
  onChange,
  min,
  max,
  required = false,
  disabled = false,
  className = '',
  placeholder,
  ...props
}, ref) => {
  return (
    <input
      ref={ref}
      type="date"
      id={id}
      name={name}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      min={min}
      max={max}
      required={required}
      disabled={disabled}
      placeholder={placeholder}
      className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white ${className}`}
      {...props}
    />
  )
})

DatePicker.displayName = 'DatePicker'

export default DatePicker