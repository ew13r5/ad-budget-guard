import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AccountCard } from '../AccountCard'
import { AccountMode } from '@/api/types'
import { describe, it, expect } from 'vitest'

function renderCard(props: Partial<Parameters<typeof AccountCard>[0]> = {}) {
  const defaults = {
    id: 'test-1',
    name: 'Test Account',
    subtitle: 'Test Subtitle',
    mode: AccountMode.simulation,
    spend: 100,
    budget: 200,
  }
  return render(
    <MemoryRouter>
      <AccountCard {...defaults} {...props} />
    </MemoryRouter>
  )
}

describe('AccountCard', () => {
  it('renders account name', () => {
    renderCard({ name: 'Client-Alpha' })
    expect(screen.getByText('Client-Alpha')).toBeInTheDocument()
  })

  it('renders formatted spend amount', () => {
    renderCard({ spend: 174.2 })
    expect(screen.getByText('$174.20')).toBeInTheDocument()
  })

  it('shows alert badge when alert provided', () => {
    renderCard({ alert: 'Budget exceeded' })
    expect(screen.getByText('Budget exceeded')).toBeInTheDocument()
  })

  it('renders mode badge', () => {
    renderCard({ mode: AccountMode.simulation })
    expect(screen.getByText('simulation')).toBeInTheDocument()
  })

  it('renders budget amount', () => {
    renderCard({ budget: 500 })
    expect(screen.getByText('/ $500')).toBeInTheDocument()
  })
})
