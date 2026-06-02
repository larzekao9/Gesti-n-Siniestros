import apiClient from './client'
import type {
  TrafficReport,
  TrafficReportListResponse,
  TrafficReportCreatePayload,
  TrafficReportUpdatePayload,
} from '@/types/traffic-report'

export const trafficReportsApi = {
  listForClaim: (claimId: string, params?: { page?: number; limit?: number }): Promise<TrafficReportListResponse> =>
    apiClient.get<TrafficReportListResponse>('/traffic-reports', { params: { claim_id: claimId, ...params } }).then((r) => r.data),

  create: (claimId: string, data: TrafficReportCreatePayload): Promise<TrafficReport> =>
    apiClient.post<TrafficReport>(`/traffic-reports?claim_id=${claimId}`, data).then((r) => r.data),

  update: (reportId: string, data: TrafficReportUpdatePayload): Promise<TrafficReport> =>
    apiClient.put<TrafficReport>(`/traffic-reports/${reportId}`, data).then((r) => r.data),

  delete: (reportId: string): Promise<void> =>
    apiClient.delete(`/traffic-reports/${reportId}`).then(() => undefined),
}
