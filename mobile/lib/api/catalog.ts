import { api } from './client'
import type { Policy, Vehicle } from '@/types/catalog'

export async function listMyVehicles(): Promise<Vehicle[]> {
  const { data } = await api.get('/me/vehicles')
  return data
}

export async function listMyPolicies(): Promise<Policy[]> {
  const { data } = await api.get('/me/policies')
  return data
}
