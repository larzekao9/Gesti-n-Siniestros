import apiClient from './client'
import type {
  AnalystProductivityResponse,
  AnalyticsFilters,
  CoverageDistributionResponse,
  KPIs,
  StatusDistributionResponse,
  TimelineResponse,
} from '@/types/analytics'

export const analyticsApi = {
  kpis: (params?: AnalyticsFilters): Promise<KPIs> =>
    apiClient.get<KPIs>('/analytics/kpis', { params }).then((r) => r.data),

  statusDistribution: (params?: AnalyticsFilters): Promise<StatusDistributionResponse> =>
    apiClient
      .get<StatusDistributionResponse>('/analytics/status-distribution', { params })
      .then((r) => r.data),

  timeline: (params?: AnalyticsFilters): Promise<TimelineResponse> =>
    apiClient.get<TimelineResponse>('/analytics/timeline', { params }).then((r) => r.data),

  coverageDistribution: (): Promise<CoverageDistributionResponse> =>
    apiClient
      .get<CoverageDistributionResponse>('/analytics/coverage-distribution')
      .then((r) => r.data),

  analystProductivity: (params?: AnalyticsFilters): Promise<AnalystProductivityResponse> =>
    apiClient
      .get<AnalystProductivityResponse>('/analytics/analyst-productivity', { params })
      .then((r) => r.data),
}
