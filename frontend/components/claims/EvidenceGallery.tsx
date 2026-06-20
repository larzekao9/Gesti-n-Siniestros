'use client'

import { useState } from 'react'
import { Download, Eye, Image, Film, FileText, File, Gauge } from 'lucide-react'
import { evidencesApi } from '@/lib/api/evidences'
import { Button } from '@/components/ui/button'
import type { Evidence } from '@/types/evidence'

interface EvidenceGalleryProps {
  items: Evidence[]
  loading?: boolean
}

// CU-35: severidad de daño estimada on-device por la app del asegurado.
// Mismo umbral de confianza que mobile/backend: por debajo no se muestra (F-A1).
// El modelo YOLO tiene 3 clases (Leve/Moderado/Severo) — ya no existe "Sin daño".
const DAMAGE_CONF_MIN = 0.65
const SEV_RANK: Record<string, number> = { Leve: 0, Moderado: 1, Severo: 2 }
const SEV_STYLE: Record<string, string> = {
  Leve: 'bg-emerald-100 text-emerald-700',
  Moderado: 'bg-amber-100 text-amber-700',
  Severo: 'bg-red-100 text-red-700',
}
const SEV_ACCENT: Record<string, string> = {
  Leve: 'border-emerald-400 text-emerald-600',
  Moderado: 'border-amber-400 text-amber-600',
  Severo: 'border-red-400 text-red-600',
}

type DamageClassification = { severidad: string; confianza: number }

/** Lee la clasificación on-device de una evidencia, si supera el umbral. */
function getDamage(item: Evidence): DamageClassification | null {
  const dc = item.metadata?.damage_classification as DamageClassification | undefined
  if (!dc || typeof dc.severidad !== 'string' || typeof dc.confianza !== 'number') return null
  if (dc.confianza < DAMAGE_CONF_MIN) return null
  return dc
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

  const damaged = items.map(getDamage).filter((d): d is DamageClassification => d !== null)
  const maxSev = damaged.length
    ? damaged.reduce((best, d) => ((SEV_RANK[d.severidad] ?? 0) > (SEV_RANK[best.severidad] ?? 0) ? d : best))
    : null

  return (
    <>
      {maxSev && (
        <div className={`mb-4 flex items-start gap-3 rounded-lg border border-slate-200 border-l-4 bg-white px-4 py-3 shadow-sm ${SEV_ACCENT[maxSev.severidad] ?? 'border-slate-300'}`}>
          <Gauge className="mt-0.5 h-5 w-5 shrink-0" />
          <div className="text-slate-700">
            <p className="text-[15px] font-semibold">
              Severidad de los daños: {maxSev.severidad}
            </p>
            <p className="mt-1 text-sm leading-snug text-slate-500">
              El asegurado tomó {damaged.length === 1 ? 'una foto' : `${damaged.length} fotos`} del
              siniestro y su teléfono estimó este nivel de daño al instante. Te sirve como referencia
              para priorizar la revisión; la palabra final es tuya.
            </p>
          </div>
        </div>
      )}
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
              {item.metadata && item.type === 'technical_report' && (() => {
                // DT-20: tipar el metadata JSONB del peritaje en vez de renderizar `unknown`.
                const meta = item.metadata as { perito_nombre?: string; monto_estimado?: number }
                return (
                  <div className="mt-1 text-xs text-slate-500">
                    {meta.perito_nombre ? <p>Perito: {meta.perito_nombre}</p> : null}
                    {meta.monto_estimado != null ? <p>Monto: Bs {meta.monto_estimado.toFixed(2)}</p> : null}
                  </div>
                )
              })()}
              {(() => {
                // CU-35: severidad estimada on-device por la app del asegurado.
                const dmg = getDamage(item)
                return dmg ? (
                  <span
                    className={`mt-1 inline-block rounded px-2 py-0.5 text-[11px] font-semibold ${SEV_STYLE[dmg.severidad] ?? 'bg-slate-100 text-slate-600'}`}
                    title={`Nivel de daño estimado por el teléfono del asegurado a partir de esta foto (${Math.round(dmg.confianza * 100)}% de certeza).`}
                  >
                    Daño {dmg.severidad.toLowerCase()} · {Math.round(dmg.confianza * 100)}%
                  </span>
                ) : null
              })()}
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
