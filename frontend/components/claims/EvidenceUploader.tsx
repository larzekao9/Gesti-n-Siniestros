'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, Loader2, FileText, Image, Film, File } from 'lucide-react'
import { toast } from 'sonner'
import { evidencesApi } from '@/lib/api/evidences'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import type { Evidence } from '@/types/evidence'

const EVIDENCE_TYPES = [
  { value: 'photo', label: 'Foto' },
  { value: 'video', label: 'Video' },
  { value: 'invoice', label: 'Factura' },
  { value: 'technical_report', label: 'Informe técnico / Peritaje' },
  { value: 'sketch', label: 'Croquis' },
  { value: 'police_report', label: 'Acta de tránsito' },
  { value: 'personal_doc', label: 'Documento personal' },
  { value: 'other', label: 'Otro' },
]

const MIME_TO_TYPE: Record<string, string> = {
  'image/jpeg': 'photo',
  'image/png': 'photo',
  'image/gif': 'photo',
  'image/webp': 'photo',
  'video/mp4': 'video',
  'video/quicktime': 'video',
  'application/pdf': 'invoice',
}

interface EvidenceUploaderProps {
  subjectType: 'claim' | 'claim_request'
  subjectId: string
  documentRequestId?: string | null
  defaultType?: string
  showPeritajeFields?: boolean
  onUploaded?: (evidence: Evidence) => void
}

export default function EvidenceUploader({
  subjectType,
  subjectId,
  documentRequestId,
  defaultType,
  showPeritajeFields,
  onUploaded,
}: EvidenceUploaderProps) {
  const [selectedType, setSelectedType] = useState(defaultType || 'photo')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [pendingFiles, setPendingFiles] = useState<File[]>([])

  // Peritaje fields
  const [peritoNombre, setPeritoNombre] = useState('')
  const [peritoDocumento, setPeritoDocumento] = useState('')
  const [fechaPeritaje, setFechaPeritaje] = useState('')
  const [montoEstimado, setMontoEstimado] = useState('')

  const onDrop = useCallback((accepted: File[]) => {
    setPendingFiles(accepted)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    maxSize: 50 * 1024 * 1024,
  })

  const uploadFile = async (file: File) => {
    try {
      const presigned = await evidencesApi.presign({
        subject_type: subjectType,
        subject_id: subjectId,
        type: selectedType,
        file_name: file.name,
        mime_type: file.type || 'application/octet-stream',
        file_size: file.size,
      })

      await evidencesApi.uploadFile(presigned.upload_url, file, (pct) => setProgress(pct))

      const metadata: Record<string, unknown> | undefined =
        selectedType === 'technical_report' && showPeritajeFields
          ? {
              perito_nombre: peritoNombre || undefined,
              perito_documento: peritoDocumento || undefined,
              fecha_peritaje: fechaPeritaje || undefined,
              monto_estimado: montoEstimado ? parseFloat(montoEstimado) : undefined,
            }
          : undefined

      const registered = await evidencesApi.register({
        subject_type: subjectType,
        subject_id: subjectId,
        s3_key: presigned.s3_key,
        type: selectedType,
        file_name: file.name,
        mime_type: file.type || 'application/octet-stream',
        file_size: file.size,
        metadata,
        document_request_id: documentRequestId || null,
      })

      toast.success(`"${file.name}" subido`)
      onUploaded?.(registered)
    } catch {
      toast.error(`Error al subir "${file.name}"`)
    }
  }

  const handleUploadAll = async () => {
    if (pendingFiles.length === 0) return
    setUploading(true)
    for (const file of pendingFiles) {
      setProgress(0)
      await uploadFile(file)
    }
    setPendingFiles([])
    setUploading(false)
    setPeritoNombre('')
    setPeritoDocumento('')
    setFechaPeritaje('')
    setMontoEstimado('')
  }

  const removeFile = (idx: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== idx))
  }

  const getFileIcon = (mime: string) => {
    if (mime.startsWith('image/')) return <Image className="h-5 w-5" />
    if (mime.startsWith('video/')) return <Film className="h-5 w-5" />
    if (mime === 'application/pdf') return <FileText className="h-5 w-5" />
    return <File className="h-5 w-5" />
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-3 items-end">
        <div className="w-48">
          <Label>Tipo de evidencia</Label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="mt-1 block w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm"
          >
            {EVIDENCE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
        {selectedType === 'technical_report' && showPeritajeFields && (
          <>
            <div><Label>Perito</Label><input type="text" value={peritoNombre} onChange={(e) => setPeritoNombre(e.target.value)} placeholder="Nombre del perito" className="mt-1 block w-full rounded-md border border-slate-200 px-3 py-2 text-sm shadow-sm" /></div>
            <div><Label>Doc. Perito</Label><input type="text" value={peritoDocumento} onChange={(e) => setPeritoDocumento(e.target.value)} placeholder="CI/NIT" className="mt-1 block w-full rounded-md border border-slate-200 px-3 py-2 text-sm shadow-sm" /></div>
            <div><Label>Fecha peritaje</Label><input type="date" value={fechaPeritaje} onChange={(e) => setFechaPeritaje(e.target.value)} className="mt-1 block w-full rounded-md border border-slate-200 px-3 py-2 text-sm shadow-sm" /></div>
            <div><Label>Monto est. (Bs)</Label><input type="number" value={montoEstimado} onChange={(e) => setMontoEstimado(e.target.value)} placeholder="0.00" className="mt-1 block w-full rounded-md border border-slate-200 px-3 py-2 text-sm shadow-sm" /></div>
          </>
        )}
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-400 bg-blue-50' : 'border-slate-300 hover:border-slate-400'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-8 w-8 text-slate-400" />
        <p className="mt-2 text-sm text-slate-500">
          {isDragActive ? 'Soltá los archivos aquí' : 'Arrastrá archivos o hacé click para seleccionar'}
        </p>
        <p className="text-xs text-slate-400 mt-1">Máximo 50 MB por archivo</p>
      </div>

      {pendingFiles.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-700">{pendingFiles.length} archivo(s) pendiente(s)</span>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={() => setPendingFiles([])}>Limpiar</Button>
              <Button size="sm" onClick={handleUploadAll} disabled={uploading}>
                {uploading ? <><Loader2 className="h-4 w-4 animate-spin mr-1" /> Subiendo... {progress > 0 && `${progress}%`}</> : 'Subir todo'}
              </Button>
            </div>
          </div>
          {pendingFiles.map((file, i) => (
            <div key={i} className="flex items-center gap-3 px-3 py-2 bg-slate-50 rounded border border-slate-200">
              {getFileIcon(file.type)}
              <span className="text-sm flex-1 truncate">{file.name}</span>
              <span className="text-xs text-slate-400">{(file.size / 1024).toFixed(0)} KB</span>
              {!uploading && (
                <button onClick={() => removeFile(i)} className="text-slate-400 hover:text-red-500"><X className="h-4 w-4" /></button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
