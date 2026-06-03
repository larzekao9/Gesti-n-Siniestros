import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

import AuditTable from '@/components/audit/AuditTable'
import type { AuditLog } from '@/types/audit'

const log: AuditLog = {
  id: '1',
  actor_user_id: 'abcdef12-0000-0000-0000-000000000000',
  action: 'STATE_CHANGE',
  entity_type: 'claim',
  entity_id: 'c1',
  payload_diff: null,
  ip_address: '10.0.0.1',
  user_agent: null,
  tenant_id: 't1',
  created_at: '2026-05-01T10:00:00Z',
}

describe('AuditTable', () => {
  it('renders rows with humanized action labels', () => {
    render(<AuditTable logs={[log]} />)
    expect(screen.getByText('Cambio de estado')).toBeInTheDocument()
    expect(screen.getByText('claim')).toBeInTheDocument()
    expect(screen.getByText('10.0.0.1')).toBeInTheDocument()
  })

  it('shows empty state when there are no logs', () => {
    render(<AuditTable logs={[]} />)
    expect(screen.getByText(/Sin eventos para los filtros/i)).toBeInTheDocument()
  })
})
