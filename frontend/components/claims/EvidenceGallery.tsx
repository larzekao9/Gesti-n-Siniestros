'use client'

import { useState, useEffect } from 'react'
import { Download, Eye, Image, Film, FileText, File } from 'lucide-react'
import { evidencesApi } from '@/lib/api/evidences'
import { Button } from '@/components/ui/button'
import type { Evidence } from '@/types/evidence'

interface EvidenceGalleryProps {
  items: Evidence[]
  loading?: boolean
}

export default function EvidenceGallery({ items, loading }: EvidenceGalleryProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [previewItem, setPreviewItem] = useState<Evidence | null>(null)

  const getIcon = (item: Evidence) => {
    if (item.mime_type.startsWith('image/')) return <Image className="h-6 w-6" />
    if (item.mime_type.startsWith('video/')) return <Film className="h-6 w-6" />
    if (item.mime_type === 'application/pdf') return <FileText className="h-6 w-6" />
    return <File className="h-6 w-6" />
  }

  const handlePreview = async (item: Evidence) => {
    if (item.mime_type.startsWith('image/')) {
      try {
        const resp = await evidencesApi.download(item.id)
        setPreviewUrl(resp.download_url)
        setPreviewItem(item)
      } catch {
        // fallback: use the presigned download_url from the list payload
        setPreviewUrl(item.download_url || item.file_url)
        setPreviewItem(item)
      }
    }
  }

  const handleDownload = async (item: Evidence) => {
    try {
      const resp = await evidencesApi.download(item.id)
      window.open(resp.download_url, '_blank')
    } catch {
      window.open(item.download_url || item.file_url, '_blank')
    }
  }

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      photo: 'Foto', video: 'Video', invoice: 'Factura',
      technical_report: 'Peritaje', sketch: 'Croquis',
      police_report: 'Acta tránsito', personal_doc: 'Doc. personal', other: 'Otro',
    }
    return labels[type] || type
  }

  if (loading) {
    return <p className="text-slate-500 text-center py-8">Cargando evidencias...</p>
  }

  if (items.length === 0) {
    return <p className="text-slate-400 text-center py-8">Sin evidencias cargadas</p>
  }

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {items.map((item) => (
          <div key={item.id} className="border border-slate-200 rounded-lg overflow-hidden bg-white group">
            <div className="h-32 bg-slate-50 flex items-center justify-center text-slate-400">
              {item.mime_type.startsWith('image/') && item.download_url ? (
                <img
                  src={item.download_url}
                  alt={item.file_name}
                  className="h-full w-full object-cover cursor-pointer"
                  onClick={() => handlePreview(item)}
                />
              ) : (
                getIcon(item)
              )}
            </div>
            <div className="p-2">
              <p className="text-xs font-medium truncate" title={item.file_name}>{item.file_name}</p>
              <p className="text-xs text-slate-400">{getTypeLabel(item.type)} &middot; {(item.file_size / 1024).toFixed(0)} KB</p>
              {item.metadata && item.type === 'technical_report' && (
                <div className="mt-1 text-xs text-slate-500">
                  {item.metadata.perito_nombre && <p>Perito: {item.metadata.perito_nombre as string}</p>}
                  {item.metadata.monto_estimado && <p>Monto: Bs {(item.metadata.monto_estimado as number).toFixed(2)}</p>}
                </div>
              )}
              <div className="flex gap-1 mt-1">
                {item.mime_type.startsWith('image/') && (
                  <Button variant="ghost" size="sm" className="h-7 px-1" onClick={() => handlePreview(item)} title="Ver">
                    <Eye className="h-3 w-3" />
                  </Button>
                )}
                <Button variant="ghost" size="sm" className="h-7 px-1" onClick={() => handleDownload(item)} title="Descargar">
                  <Download className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {previewUrl && previewItem && (
        <div
          className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
          onClick={() => { setPreviewUrl(null); setPreviewItem(null) }}
        >
          <div className="max-w-4xl max-h-[90vh] overflow-auto bg-white rounded-lg p-2" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-2 px-1">
              <span className="text-sm font-medium">{previewItem.file_name}</span>
              <Button variant="ghost" size="sm" onClick={() => { setPreviewUrl(null); setPreviewItem(null) }}>Cerrar</Button>
            </div>
            <img src={previewUrl} alt={previewItem.file_name} className="max-w-full max-h-[80vh] object-contain rounded" />
          </div>
        </div>
      )}
    </>
  )
}
