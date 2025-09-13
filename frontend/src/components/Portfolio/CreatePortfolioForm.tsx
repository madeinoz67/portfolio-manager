import { useState } from 'react'
import { CreatePortfolioData } from '@/types/portfolio'

interface CreatePortfolioFormProps {
  onSubmit: (data: CreatePortfolioData) => Promise<boolean>
  onCancel: () => void
}

export default function CreatePortfolioForm({ onSubmit, onCancel }: CreatePortfolioFormProps) {
  const [formData, setFormData] = useState<CreatePortfolioData>({ 
    name: '', 
    description: '' 
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    const success = await onSubmit(formData)
    if (success) {
      setFormData({ name: '', description: '' })
      onCancel() // Close form on success
    }
    
    setIsSubmitting(false)
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg shadow-md border dark:border-gray-700 animate-slide-up">
      <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Create New Portfolio</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Portfolio Name
          </label>
          <input
            type="text"
            required
            maxLength={100}
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full p-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            placeholder="Enter portfolio name"
            disabled={isSubmitting}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description (optional)
          </label>
          <textarea
            maxLength={500}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full p-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            placeholder="Enter description"
            rows={3}
            disabled={isSubmitting}
          />
        </div>
        <div className="flex flex-col sm:flex-row gap-2 sm:space-x-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full sm:w-auto bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-600 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? 'Creating...' : 'Create Portfolio'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="w-full sm:w-auto bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 dark:bg-gray-500 dark:hover:bg-gray-400 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}