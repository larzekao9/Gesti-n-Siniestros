import { useQuery } from '@tanstack/react-query'

import {
  getMyClaim,
  getMyClaimRequest,
  listMyClaimRequests,
} from '../api/claim-requests'
import { listRequestEvidences } from '../api/evidences'

export const claimKeys = {
  requests: ['me', 'claim-requests'] as const,
  request: (id: string) => ['me', 'claim-request', id] as const,
  requestEvidences: (id: string) => ['me', 'claim-request', id, 'evidences'] as const,
  claim: (id: string) => ['me', 'claim', id] as const,
}

export function useMyClaimRequests() {
  return useQuery({
    queryKey: claimKeys.requests,
    queryFn: () => listMyClaimRequests(1, 50),
  })
}

export function useMyClaimRequest(id: string | undefined) {
  return useQuery({
    queryKey: claimKeys.request(id ?? ''),
    queryFn: () => getMyClaimRequest(id as string),
    enabled: !!id,
  })
}

export function useMyClaim(id: string | undefined) {
  return useQuery({
    queryKey: claimKeys.claim(id ?? ''),
    queryFn: () => getMyClaim(id as string),
    enabled: !!id,
  })
}

export function useRequestEvidences(id: string | undefined) {
  return useQuery({
    queryKey: claimKeys.requestEvidences(id ?? ''),
    queryFn: () => listRequestEvidences(id as string),
    enabled: !!id,
  })
}
