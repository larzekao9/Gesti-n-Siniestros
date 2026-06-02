import apiClient from './client'
import type {
  Evidence,
  EvidenceListResponse,
  PresignedUrlRequest,
  PresignedUrlResponse,
  EvidenceRegisterPayload,
  EvidenceDownloadUrlResponse,
} from '@/types/evidence'

export const evidencesApi = {
  presign: (data: PresignedUrlRequest): Promise<PresignedUrlResponse> =>
    apiClient.post<PresignedUrlResponse>('/evidences/presign', data).then((r) => r.data),

  register: (data: EvidenceRegisterPayload): Promise<Evidence> =>
    apiClient.post<Evidence>('/evidences', data).then((r) => r.data),

  listForClaim: (claimId: string, params?: { page?: number; limit?: number }): Promise<EvidenceListResponse> =>
    apiClient.get<EvidenceListResponse>(`/evidences/claims/${claimId}`, { params }).then((r) => r.data),

  listForRequest: (requestId: string, params?: { page?: number; limit?: number }): Promise<EvidenceListResponse> =>
    apiClient.get<EvidenceListResponse>(`/evidences/claim-requests/${requestId}`, { params }).then((r) => r.data),

  download: (evidenceId: string): Promise<EvidenceDownloadUrlResponse> =>
    apiClient.get<EvidenceDownloadUrlResponse>(`/evidences/${evidenceId}/download`).then((r) => r.data),

  uploadFile: async (uploadUrl: string, file: File, onProgress?: (pct: number) => void): Promise<void> => {
    await apiClient.put(uploadUrl, file, {
      headers: { 'Content-Type': file.type },
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded * 100) / event.total))
        }
      },
    })
  },
}
