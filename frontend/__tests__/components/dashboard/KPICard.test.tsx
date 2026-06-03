import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FileText } from 'lucide-react'

import KPICard from '@/components/dashboard/KPICard'

describe('KPICard', () => {
  it('renders label, value and hint', () => {
    render(<KPICard label="Expedientes" value={42} hint="último mes" icon={FileText} />)
    expect(screen.getByText('Expedientes')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('último mes')).toBeInTheDocument()
  })

  it('renders string values (percentages)', () => {
    render(<KPICard label="Aprobación" value="75.0%" accent="green" />)
    expect(screen.getByText('75.0%')).toBeInTheDocument()
  })
})
