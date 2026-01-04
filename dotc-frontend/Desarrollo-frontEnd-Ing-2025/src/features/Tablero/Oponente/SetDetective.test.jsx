import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent, screen } from '@testing-library/react';

vi.mock('../../../components/Carta/Carta', () => ({
  Carta: ({ onCardClick, onMouseEnter, onMouseLeave, isTargetCard, dataDiff, cartaData }) => (
    <button
      data-testid={`carta-${cartaData.card_id}`}
      data-diff={dataDiff}
      data-target={isTargetCard ? '1' : '0'}
      onClick={onCardClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >{String(cartaData.card_id)}</button>
  ),
}));

import { SetDetective } from './SetDetective.jsx';

describe('SetDetective', () => {
  const cartas = [
    { card_id: 1, set_id: 10, player_id: 99 },
    { card_id: 2, set_id: 10, player_id: 99 },
  ];

  it('renders cards and toggles hover state', () => {
    const { container } = render(<SetDetective cartasSet={cartas} targetSetId={10} onCardClick={() => {}} />);
    const wrapper = container.querySelector('.detective-set-container');
    expect(wrapper).toBeInTheDocument();
    // Initially not hovered
    expect(wrapper?.getAttribute('data-hovered')).toBe('false');

    const first = screen.getByTestId('carta-1');
    const second = screen.getByTestId('carta-2');

    // hover first card
    fireEvent.mouseEnter(first);
    expect(wrapper?.getAttribute('data-hovered')).toBe('true');
    // data-diff should reflect index - hoveredIndex
    expect(first.getAttribute('data-diff')).toBe('0');
    expect(second.getAttribute('data-diff')).toBe('1');

    // leave hover
    fireEvent.mouseLeave(first);
    expect(wrapper?.getAttribute('data-hovered')).toBe('false');
  });

  it('calls onCardClick with set_id and player_id', () => {
    const onClick = vi.fn();
    render(<SetDetective cartasSet={cartas} targetSetId={10} onCardClick={onClick} />);
    const first = screen.getByTestId('carta-1');
    fireEvent.click(first);
    expect(onClick).toHaveBeenCalledWith(10, 99);
  });

  it('marks target cards via isTargetCard', () => {
    render(<SetDetective cartasSet={cartas} targetSetId={10} onCardClick={() => {}} />);
    expect(screen.getByTestId('carta-1').getAttribute('data-target')).toBe('1');
    expect(screen.getByTestId('carta-2').getAttribute('data-target')).toBe('1');
  });
});
