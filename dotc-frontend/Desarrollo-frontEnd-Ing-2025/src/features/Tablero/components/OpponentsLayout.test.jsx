import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import { OpponentsLayout } from './OpponentsLayout.jsx';
import {
  players_game_2,
  players_game_3,
  players_game_4,
  players_game_5,
  players_game_6
} from '../constants/mockPlayers.js';

// Mock liviano del hijo para desacoplar visual
vi.mock('../Oponente/Oponente.jsx', () => ({
  Oponente: ({ playerName }) => <div data-testid="op">{playerName}</div>
}));

const getOpponentWrappers = (container) => container.querySelectorAll('.opponent');

describe('OpponentsLayout', () => {
  it('1 oponente -> center-slot', () => {
    const opponents = players_game_2.filter(p => p.id !== 1); // 1 oponente
    const { container } = render(<OpponentsLayout opponents={opponents} gameId={999} />);
    const nodes = getOpponentWrappers(container);
    expect(nodes).toHaveLength(1);
    expect(nodes[0]).toHaveClass('center-slot');
  });

  it('2 oponentes -> center-left, center-right', () => {
    const opponents = players_game_3.filter(p => p.id !== 1); // 2 oponentes
    const { container } = render(<OpponentsLayout opponents={opponents} gameId={999} />);
    const nodes = getOpponentWrappers(container);
    expect(nodes).toHaveLength(2);
    expect(nodes[0]).toHaveClass('center-left');
    expect(nodes[1]).toHaveClass('center-right');
  });
});