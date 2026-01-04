import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Control variables for mocks
let wsDeckSizeToSet = null; // null means don't touch deck, number means set via hook
let mockHandCards = null; // null => default 2 cards, or provide array
let mockIsMyTurn = true;  // controls esMiTurno from WS hook
let mockSelectionSuggestion = { visible: false, text: null }; // controls useCardSelection suggestion

vi.mock('./hooks/player/usePlayerHand.js', () => ({
  usePlayerHand: () => ({
    mano: Array.isArray(mockHandCards)
      ? mockHandCards
      : [
          { card_id: 1, card_type: 'Ariadne Oliver' },
          { card_id: 2, card_type: 'Ariadne Oliver' },
        ],
    setMano: vi.fn(),
    cargandoMano: false,
    errorMano: null,
  }),
}));

vi.mock('./hooks/game/useGameState.js', () => ({
  useGameState: () => ({
    players: [
      { player_id: 1, name: 'Yo' },
      { player_id: 2, name: 'Rival' },
    ],
    forceUpdate: vi.fn(),
  }),
}));

vi.mock('./hooks/game/useTurnActions.js', () => ({
  useTurnActions: () => ({
    robarDesdeFuente: vi.fn(async () => [{ card_id: 3 }]),
    descartarCarta: vi.fn(async () => [{ card_id: 1 }]),
    pasarTurno: vi.fn(),
  }),
}));

vi.mock('./hooks/player/usePlaySelection.js', () => ({
  usePlaySelection: () => ({
    actionType: null,
    setActionType: vi.fn(),
    play: vi.fn(async () => ({ ok: true })),
    targetPlayerId: null,
    targetSecretId: null,
    targetCardId: null,
    targetSetId: null,
    toggleTargetCard: vi.fn(),
    toggleTargetPlayer: vi.fn(),
    toggleTargetSecret: vi.fn(),
    toggleTargetSet: vi.fn(),
  }),
}));

vi.mock('./hooks/game/useTurnWebSocket.js', () => ({
  useTurnWebSocket: (opts = {}) => {
    if (typeof wsDeckSizeToSet === 'number' && typeof opts.setDeckCount === 'function') {
      // Schedule state update asynchronously to avoid setState during render
      setTimeout(() => opts.setDeckCount(wsDeckSizeToSet), 0);
    }
    return { currentTurnId: 999, esMiTurno: mockIsMyTurn };
  },
}));

vi.mock('./hooks/secrets/useSecretPlayer.js', () => ({
  usePlayerSecret: () => ({
    secretP: [
      { secret_id: 10, is_revealed: false },
      { secret_id: 11, is_revealed: false },
      { secret_id: 12, is_revealed: false },
    ],
    setSecretP: vi.fn(),
    cargandoSecreto: false,
    errorSecreto: null,
  }),
}));

// Mock new hooks added during refactor
vi.mock('./hooks/player/useCardSelection.js', () => ({
  useCardSelection: () => ({
    actionSuggestionVisible: mockSelectionSuggestion.visible,
    actionSuggestionText: mockSelectionSuggestion.text,
    puedeFormarSet: false,
    puedeJugarEvento: false,
    puedeAgregarSet: false,
    toggleSelectCard: vi.fn(),
    resetSelection: vi.fn(),
    selectionState: {},
  }),
}));

vi.mock('./hooks/sets/useSetManagement.js', () => ({
  useSetManagement: () => ({
    setPlayed: {},
    setsPropios: [],
    stolenSet: {},
    onSetPlayed: vi.fn(),
    onSetStolen: vi.fn(),
  }),
}));

vi.mock('./hooks/secrets/useRevealSecret.js', () => ({
  useRevealSecret: () => ({
    revealedSecret: {},
    onSecretRevealed: vi.fn(),
  }),
}));

vi.mock('./hooks/player/useCardLook.js', () => ({
  useCardLook: () => ({
    cardsLook: [],
    cardLookSelect: null,
    onCardLook: vi.fn(),
    toggleCardLook: vi.fn(),
    confirmCardLook: vi.fn(),
  }),
}));

// Additional new hooks used by Tablero
vi.mock('./hooks/opponents/useOpponentsData.js', () => ({
  useOpponentsData: () => ({ opponentsData: [] }),
}));

vi.mock('./hooks/game/useTableroHandlers.js', () => ({
  useTableroHandlers: () => ({
    handleRobarDraw: vi.fn(),
    handleRobarDraft: vi.fn(),
    handleRobarDiscard: vi.fn(),
    handleSelectCard: vi.fn(),
    handleDiscard: vi.fn(),
    handlePassTurn: vi.fn(),
    handlePlayAction: vi.fn(),
  }),
}));

// Make presentational children lightweight
vi.mock('./components/OpponentsLayout.jsx', () => ({
  OpponentsLayout: () => <div data-testid="opponents-layout" />,
}));
vi.mock('./components/CentroMesa.jsx', () => ({
  CentroMesa: (props) => <div data-testid="centro-mesa" data-can-draw={String(props.canDraw)} />,
}));
vi.mock('./ManoPropia/ManoPropia.jsx', () => ({
  ManoPropia: (props) => (
    <div
      data-testid="mano-propia"
      data-suggest-visible={String(!!props.actionSuggestionVisible)}
      data-suggest-text={props.actionSuggestionText || ''}
    />
  ),
}));


// After the mocks
import Tablero from './Tablero.jsx';

describe('Tablero', () => {
  beforeEach(() => {
    wsDeckSizeToSet = null;
    mockHandCards = null;
    mockIsMyTurn = true;
    mockSelectionSuggestion = { visible: false, text: null };
  });

  it('renderiza sin mostrar fin de juego por defecto y con canDraw=false', () => {
    render(<Tablero playerName="Yo" game_id={1} player_id={1} />);
    expect(screen.getByTestId('opponents-layout')).toBeInTheDocument();
    expect(screen.getByTestId('centro-mesa')).toBeInTheDocument();
    expect(screen.getByTestId('mano-propia')).toBeInTheDocument();
    expect(screen.queryByText('¡Fin del juego!')).not.toBeInTheDocument();
    expect(screen.getByTestId('centro-mesa')).toHaveAttribute('data-can-draw', 'false');
  });

  it('muestra fin de juego cuando el mazo llega a 0', async () => {
    wsDeckSizeToSet = 0;
    render(<Tablero playerName="Yo" game_id={1} player_id={1} />);
    // El componente actual muestra una tarjeta de fin con el título "El Asesino Ganó"
    expect(await screen.findByText('El Asesino Ganó')).toBeInTheDocument();
  });

  it('deshabilita robar cuando la mano tiene 6 o más cartas', () => {
    mockHandCards = [1, 2, 3, 4, 5, 6].map((n) => ({ card_id: n, card_type: 'Ariadne Oliver' }));
    render(<Tablero playerName="Yo" game_id={1} player_id={1} />);
    expect(screen.getByTestId('centro-mesa')).toHaveAttribute('data-can-draw', 'false');
  });

  it('deshabilita robar cuando no es mi turno', () => {
    mockIsMyTurn = false;
    render(<Tablero playerName="Yo" game_id={1} player_id={1} />);
    expect(screen.getByTestId('centro-mesa')).toHaveAttribute('data-can-draw', 'false');
  });

  it('propaga sugerencia de acción a ManoPropia', () => {
    mockSelectionSuggestion = { visible: true, text: 'Ariadne Oliver - ¡Puedes revelar un secreto!' };
    render(<Tablero playerName="Yo" game_id={1} player_id={1} />);
    const mano = screen.getByTestId('mano-propia');
    expect(mano).toHaveAttribute('data-suggest-visible', 'true');
    expect(mano).toHaveAttribute('data-suggest-text');
    expect(mano.getAttribute('data-suggest-text')).toContain('Ariadne Oliver');
  });
});
