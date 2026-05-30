'use client'

import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from './button'
import { cn } from '@/lib/utils'

export interface Column<T> {
  header: string
  accessor: keyof T | ((row: T) => React.ReactNode)
  className?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  page: number
  total: number
  limit: number
  onPageChange: (page: number) => void
  isLoading?: boolean
  emptyMessage?: string
  getRowKey: (row: T) => string
}

export function DataTable<T>({
  columns,
  data,
  page,
  total,
  limit,
  onPageChange,
  isLoading,
  emptyMessage = 'No se encontraron resultados.',
  getRowKey,
}: DataTableProps<T>) {
  const totalPages = Math.max(1, Math.ceil(total / limit))

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-slate-500 text-sm">
        Cargando...
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-slate-500 text-sm">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-md border border-slate-200">
      <table className="w-full text-sm text-left">
        <thead className="bg-slate-50 border-b border-slate-200">
          <tr>
            {columns.map((col, i) => (
              <th
                key={i}
                className={cn('px-4 py-3 font-medium text-slate-600', col.className)}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {data.map((row) => (
            <tr key={getRowKey(row)} className="hover:bg-slate-50/50 transition-colors">
              {columns.map((col, j) => {
                const value =
                  typeof col.accessor === 'function'
                    ? col.accessor(row)
                    : String(row[col.accessor as keyof T] ?? '')
                return (
                  <td key={j} className={cn('px-4 py-3', col.className)}>
                    {value}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200">
          <span className="text-xs text-slate-500">
            Página {page} de {totalPages} ({total} resultados)
          </span>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
