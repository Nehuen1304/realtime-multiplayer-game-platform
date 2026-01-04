import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Oponente } from './Oponente.jsx';

// Mock de Carta para simplificar
vi.mock('../../../components/Carta/Carta.jsx', () => ({
  Carta: ({ className, onCardClick }) => (
    <div data-testid="card" className={className} onClick={onCardClick} />
  ),
}));

// Mock de Carta_Secreta para identificar secretos
vi.mock('../../../components/Carta/Carta_Secreta.jsx', () => ({
  Carta_Secreta: ({ className = '', onClick, dataSecret }) => (
    <div
      data-testid="secret-card"
      className={`secret-card ${className}`}
      onClick={onClick}
      data-secret-id={dataSecret?.secret_id || dataSecret?.id}
    />
  ),
}));

// Mock de SetDetective para evitar errores
vi.mock('./SetDetective.jsx', () => ({
  SetDetective: () => <div data-testid="set-detective" />,
}));

beforeEach(() => {
  // no-op
});

describe('Oponente', () => {
  const defaultHand = [
    { card_id: 1, player_id: 2 },
    { card_id: 2, player_id: 2 },
    { card_id: 3, player_id: 2 },
    { card_id: 4, player_id: 2 },
    { card_id: 5, player_id: 2 },
    { card_id: 6, player_id: 2 },
  ];
  const defaultSecrets = [
    { secret_id: 's1', is_revealed: false, player_id: 2 },
    { secret_id: 's2', is_revealed: false, player_id: 2 },
    { secret_id: 's3', is_revealed: false, player_id: 2 },
  ];
  const makePlaySel = (overrides = {}) => ({
    toggleTargetCard: vi.fn(),
    toggleTargetSecret: vi.fn(),
    toggleTargetPlayer: vi.fn(),
    toggleTargetSet: vi.fn(),
    targetPlayerId: null,
    targetSecretId: null,
    targetCardId: null,
    targetSetId: null,
    ...overrides,
  });

  it('renderiza la mano, secretos y nombre con props', async () => {
    const playSel = makePlaySel();
    render(<Oponente playerName="Rival A" playerId={2} handCards={defaultHand} secretCards={defaultSecrets} detectiveSets={[]} playSel={playSel} />);

    await waitFor(() => {
      const handCards = screen.getAllByTestId('card');
      expect(handCards.length).toBe(6);
    });
    await waitFor(() => {
      const secrets = screen.getAllByTestId('secret-card');
      expect(secrets.length).toBe(3);
    });
    expect(screen.getByText('Rival A')).toBeInTheDocument();
  });

  it('llama a toggleTargetCard al hacer click en una carta', async () => {
    const playSel = makePlaySel();
    render(
      <Oponente
        playerName="Rival D"
        playerId={2}
        handCards={defaultHand}
        secretCards={defaultSecrets}
        detectiveSets={[]}
        playSel={playSel}
      />
    );
    await waitFor(() => {
      const handCards = screen.getAllByTestId('card');
      expect(handCards.length).toBe(6);
    });
    // Click en la primera carta
    screen.getAllByTestId('card')[0].click();
    expect(playSel.toggleTargetCard).toHaveBeenCalled();
  });

  it('llama a toggleTargetSecret al hacer click en un secreto', async () => {
    const playSel = makePlaySel();
    render(
      <Oponente
        playerName="Rival E"
        playerId={2}
        handCards={defaultHand}
        secretCards={defaultSecrets}
        detectiveSets={[]}
        playSel={playSel}
      />
    );
    await waitFor(() => {
      const secrets = screen.getAllByTestId('secret-card');
      expect(secrets.length).toBe(3);
    });
    // Click en el primer secreto
    screen.getAllByTestId('secret-card')[0].click();
    expect(playSel.toggleTargetSecret).toHaveBeenCalled();
  });

  it('llama a toggleTargetPlayer al hacer click en el nombre', async () => {
    const playSel = makePlaySel();
    render(
      <Oponente
        playerName="Rival F"
        playerId={2}
        handCards={defaultHand}
        secretCards={defaultSecrets}
        detectiveSets={[]}
        playSel={playSel}
      />
    );
    await waitFor(() => {
      expect(screen.getByText('Rival F')).toBeInTheDocument();
    });
    // Click en el área de info
    screen.getByText('Rival F').parentElement.click();
    expect(playSel.toggleTargetPlayer).toHaveBeenCalledWith(2);
  });

  it('renderiza sets de detectives cuando recibe detectiveSets', async () => {
    const playSel = makePlaySel();
    const { rerender } = render(
      <Oponente playerName="Rival G" playerId={2} handCards={defaultHand} secretCards={defaultSecrets} detectiveSets={[]} playSel={playSel} />
    );

    // Inicialmente no hay sets
    await waitFor(() => {
      expect(screen.queryAllByTestId('set-detective').length).toBe(0);
    });

    // Llega un set
    rerender(
      <Oponente
        playerName="Rival G"
        playerId={2}
        handCards={defaultHand}
        secretCards={defaultSecrets}
        detectiveSets={[[{ set_id: 101, card_type: 'Ariadne Oliver' }]]}
        playSel={playSel}
      />
    );

    await waitFor(() => {
      expect(screen.getAllByTestId('set-detective').length).toBe(1);
    });

    // Llega otro set distinto
    rerender(
      <Oponente
        playerName="Rival G"
        playerId={2}
        handCards={defaultHand}
        secretCards={defaultSecrets}
        detectiveSets={[[{ set_id: 101 }], [{ set_id: 102, card_type: 'Tommy Beresford' }]]}
        playSel={playSel}
      />
    );

    await waitFor(() => {
      expect(screen.getAllByTestId('set-detective').length).toBe(2);
    });
  });

  it('pasa correctamente los props de targetCardId y targetSecretId', async () => {
    const playSel = makePlaySel({ targetCardId: 2, targetSecretId: 's2' });
    render(
      <Oponente
        playerName="Rival J"
        playerId={2}
        handCards={defaultHand}
        secretCards={defaultSecrets}
        detectiveSets={[]}
        playSel={playSel}
      />
    );
    await waitFor(() => {
      const handCards = screen.getAllByTestId('card');
      expect(handCards.length).toBe(6);
      // No hay error si se renderizan con los props
    });
    await waitFor(() => {
      const secrets = screen.getAllByTestId('secret-card');
      expect(secrets.length).toBe(3);
    });
  });

  it('renderiza correctamente cuando isTurn es true', async () => {
    const playSel = makePlaySel();
    render(
      <Oponente
        playerName="Rival K"
        playerId={2}
        isTurn={true}
        handCards={defaultHand}
        secretCards={defaultSecrets}
        detectiveSets={[]}
        playSel={playSel}
      />
    );
    await waitFor(() => {
      expect(screen.getByText('Rival K')).toBeInTheDocument();
      const infoDiv = screen.getByText('Rival K').parentElement;
      expect(infoDiv.className).toMatch(/oponente-turn/);
    });
  });

  it('renderiza correctamente cuando isTurn es false', async () => {
    const playSel = makePlaySel();
    render(
      <Oponente
        playerName="Rival L"
        playerId={2}
        isTurn={false}
        handCards={defaultHand}
        secretCards={defaultSecrets}
        detectiveSets={[]}
        playSel={playSel}
      />
    );
    await waitFor(() => {
      expect(screen.getByText('Rival L')).toBeInTheDocument();
      const infoDiv = screen.getByText('Rival L').parentElement;
      expect(infoDiv.className).not.toMatch(/oponente-turn/);
    });
  });
});