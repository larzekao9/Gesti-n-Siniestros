import { useQuery } from '@tanstack/react-query'

import { listMyPolicies, listMyVehicles } from '../api/catalog'

export function useMyVehicles() {
  return useQuery({ queryKey: ['me', 'vehicles'], queryFn: listMyVehicles })
}

export function useMyPolicies() {
  return useQuery({ queryKey: ['me', 'policies'], queryFn: listMyPolicies })
}
