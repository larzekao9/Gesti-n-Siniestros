// Catálogo del asegurado para el wizard (espejo parcial de PolicyOut/VehicleOut).

export interface Policy {
  id: string
  policy_number: string
  policyholder_id: string
  valid_from: string
  valid_to: string
  coverage_type: string
  exclusions: string | null
  status: string
}

export interface Vehicle {
  id: string
  plate: string
  make: string
  model: string
  year: number
  color: string | null
  vehicle_type: string
  policy_id: string
  status: string
}
