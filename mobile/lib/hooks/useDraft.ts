import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  createDraft,
  deleteDraft,
  submitClaimRequest,
  updateDraft,
} from '../api/claim-requests'
import type {
  ClaimRequestCreatePayload,
  ClaimRequestUpdatePayload,
} from '@/types/claim-request'
import { claimKeys } from './useClaims'

export function useCreateDraft() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ClaimRequestCreatePayload) => createDraft(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: claimKeys.requests }),
  })
}

export function useUpdateDraft(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ClaimRequestUpdatePayload) => updateDraft(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: claimKeys.request(id) })
      qc.invalidateQueries({ queryKey: claimKeys.requests })
    },
  })
}

export function useDeleteDraft() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteDraft(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: claimKeys.requests }),
  })
}

export function useSubmitClaimRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => submitClaimRequest(id),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: claimKeys.request(id) })
      qc.invalidateQueries({ queryKey: claimKeys.requests })
    },
  })
}
