import { render } from '@testing-library/react-native'

import { StatusBadge } from '@/components/ui/StatusBadge'

describe('StatusBadge', () => {
  it('muestra la etiqueta del estado (no solo color)', () => {
    const { getByText } = render(<StatusBadge status="submitted" />)
    expect(getByText('Enviada')).toBeTruthy()
  })

  it('expone un accessibilityLabel descriptivo', () => {
    const { getByLabelText } = render(<StatusBadge status="approved" />)
    expect(getByLabelText('Estado: Aprobado')).toBeTruthy()
  })
})
