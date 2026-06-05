import { api } from './client'
import type {
  Evidence,
  EvidenceListResponse,
  EvidenceType,
  PresignedUrlResponse,
} from '@/types/evidence'

export interface LocalAsset {
  uri: string
  fileName: string
  mimeType: string
  fileSize: number
  type: EvidenceType
}

/** Sube el binario a la URL presignada de S3 (PUT directo). */
async function putToS3(uploadUrl: string, asset: LocalAsset): Promise<void> {
  const res = await fetch(asset.uri)
  const blob = await res.blob()
  const put = await fetch(uploadUrl, {
    method: 'PUT',
    headers: { 'Content-Type': asset.mimeType },
    body: blob,
  })
  if (!put.ok) {
    throw new Error(`Fallo la subida del archivo (HTTP ${put.status})`)
  }
}

/** Flujo completo de evidencia del asegurado (CU-04): presign → PUT S3 → register. */
export async function uploadRequestEvidence(
  requestId: string,
  asset: LocalAsset
): Promise<Evidence> {
  const { data: presign } = await api.post<PresignedUrlResponse>(
    `/me/claim-requests/${requestId}/evidences/presign`,
    {
      type: asset.type,
      file_name: asset.fileName,
      mime_type: asset.mimeType,
      file_size: asset.fileSize,
    }
  )

  await putToS3(presign.upload_url, asset)

  const { data: evidence } = await api.post<Evidence>(
    `/me/claim-requests/${requestId}/evidences`,
    {
      s3_key: presign.s3_key,
      type: asset.type,
      file_name: asset.fileName,
      mime_type: asset.mimeType,
      file_size: asset.fileSize,
    }
  )
  return evidence
}

export async function listRequestEvidences(
  requestId: string
): Promise<EvidenceListResponse> {
  const { data } = await api.get(`/me/claim-requests/${requestId}/evidences`)
  return data
}

/** Subida de documentación solicitada (CU-08): presign → PUT S3 → register, lo
 * que adjunta la evidencia al claim y cierra el document_request. */
export async function submitDocument(
  docRequestId: string,
  asset: LocalAsset
): Promise<Evidence> {
  const { data: presign } = await api.post<PresignedUrlResponse>(
    `/me/document-requests/${docRequestId}/evidences/presign`,
    {
      type: asset.type,
      file_name: asset.fileName,
      mime_type: asset.mimeType,
      file_size: asset.fileSize,
    }
  )

  await putToS3(presign.upload_url, asset)

  const { data: evidence } = await api.post<Evidence>(
    `/me/document-requests/${docRequestId}/evidences`,
    {
      s3_key: presign.s3_key,
      type: asset.type,
      file_name: asset.fileName,
      mime_type: asset.mimeType,
      file_size: asset.fileSize,
      document_request_id: docRequestId,
    }
  )
  return evidence
}
