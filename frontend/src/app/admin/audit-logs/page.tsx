'use client'

import { AuditLogTable } from '@/components/admin/AuditLogTable'

export default function AuditLogsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Audit Logs</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Track all portfolio and transaction events across the system. Monitor user activity and system changes for security and compliance.
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <AuditLogTable />
      </div>
    </div>
  )
}