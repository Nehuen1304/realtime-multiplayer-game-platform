import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
vi.mock('../../tableroService.js', () => ({
  getManoJugador: vi.fn(async () => ({ cards: [{ card_id: 9 }] })),
  exchangeCard: vi.fn(async () => ({ ok: true })),
  sendVote: vi.fn(async () => ({ ok: true })),
}));
import * as tableroService from '../../tableroService.js';
import { useTableroHandlers } from './useTableroHandlers.js';

describe('useTableroHandlers', () => {
  beforeEach(() => vi.clearAllMocks());

  const setup = (over = {}) => renderHook(() =>
    useTableroHandlers({
      mano: [{ card_id: 1 }],
      setMano: vi.fn(),
      esMiTurno: true,
      robarDesdeFuente: vi.fn(async () => [{ card_id: 2 }]),
      setAlerta: vi.fn(),
      selectedCardIds: [1],
      descartarCarta: vi.fn(async () => [{ card_id: 3 }]),
      accionRealizada: true,
      toggleSelectCard: vi.fn(),
      pasarTurno: vi.fn(),
      game_id: 7,
      player_id: 8,
      playSel: { play: vi.fn(async () => ({ ok: true })), targetCardId: 5, targetPlayerId: 4 },
      nsfWindowOpen: false,
      removeOpponentCardsFromHand: vi.fn(),
      setActionSuggestionVisible: vi.fn(),
      tradeRequest: { request_id: 1 },
      setTradeRequest: vi.fn(),
      setVotePrompt: vi.fn(),
      ...over,
    })
  );

  it('handlePlayAction actualiza mano', async () => {
    const { result } = setup();
    await act(async () => {
      const r = await result.current.handlePlayAction();
      expect(r).toEqual({ ok: true });
    });
    expect(tableroService.getManoJugador).toHaveBeenCalledWith(7, 8);
  });

  it('handleSendTradeCard llama exchangeCard', async () => {
    const { result } = setup();
    await act(async () => {
      const r = await result.current.handleSendTradeCard();
      expect(r).toEqual({ ok: true });
    });
    expect(tableroService.exchangeCard).toHaveBeenCalled();
  });

  it('handleSendVote llama sendVote', async () => {
    const { result } = setup();
    await act(async () => {
      await result.current.handleSendVote();
    });
    expect(tableroService.sendVote).toHaveBeenCalledWith(7, 8, 4);
  });

  it('handleSelectCard bloquea cuando acción realizada y no NSF', () => {
    const toggle = vi.fn();
    const { result } = setup({ toggleSelectCard: toggle, accionRealizada: true, nsfWindowOpen: false });
    act(() => {
      result.current.handleSelectCard({ card_id: 1, card_type: 'Otra' });
    });
    expect(toggle).not.toHaveBeenCalled();
  });

  it('handleSelectCard permite NSF preselección', () => {
    const toggle = vi.fn();
    const { result } = setup({ toggleSelectCard: toggle, accionRealizada: true, nsfWindowOpen: false });
    act(() => {
      result.current.handleSelectCard({ card_id: 2, card_type: 'Not So Fast' });
    });
    expect(toggle).toHaveBeenCalled();
  });
});