
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createGameLogicHandlers } from './gameLogic.js';

describe('createGameLogicHandlers', () => {
  let callbacks;
  let handlers;

  beforeEach(() => {
    callbacks = {
      onGameStartedLobby: vi.fn(),
      updateLobbyPlayers: vi.fn(),
      onGameCancel: vi.fn(),
      onSetCurrentTurnId: vi.fn(),
      onSetDeckCount: vi.fn(),
      onSetDraftCards: vi.fn(),
      onSetDiscardCard: vi.fn(),
      onLobbyGameInfoUpdate: vi.fn(),
      onSetSetPlayed: vi.fn(),
      onStolenSet: vi.fn(),
      onCardsPlayed: vi.fn(),
      onPromptReveal: vi.fn(),
      onSecretRevealed: vi.fn(),
      onSecretStolen: vi.fn(),
      onSecretHidden: vi.fn(),
      onPromptDrawFromDiscard: vi.fn(),
      onSocialDisgraceApplied: vi.fn(),
      onSocialDisgraceRemoved: vi.fn(),
      onCardsNSFDiscarded: vi.fn(),
      onGameOver: vi.fn(),
      onVoteStarted: vi.fn(),
      onNsfWindowOpen: vi.fn(),
      onNsfWindowClose: vi.fn(),
      onOpponentDiscarded: vi.fn(),
    };
    handlers = createGameLogicHandlers(callbacks);
    vi.clearAllMocks();
  });

  it('calls onSetDiscardCard and onOpponentDiscarded in handleCardDiscarded', () => {
    const payload = { player_id: 1, card: { card_id: 2, foo: 'bar' } };
    handlers.handleCardDiscarded(payload, 'INGAME');
    expect(callbacks.onSetDiscardCard).toHaveBeenCalledWith({ card_id: 2, foo: 'bar', is_revealed: true });
    expect(callbacks.onOpponentDiscarded).toHaveBeenCalledWith(1, 2);
  });

  it('calls onSetSetPlayed in handleCardPlayed', () => {
    handlers.handleCardPlayed({ player_id: 1, cards_played: [1, 2] }, 'INGAME');
    expect(callbacks.onSetSetPlayed).toHaveBeenCalledWith({ player_id: 1, cards_played: [1, 2] });
  });

  it('calls onCardsPlayed and onSetSetPlayed in handleCardsPlayed', () => {
    const payload = { player_id: 1, cards_played: [1, 2], is_cancellable: true, action_id: 'a', player_name: 'Bob' };
    handlers.handleCardsPlayed(payload, 'INGAME');
    expect(callbacks.onCardsPlayed).toHaveBeenCalledWith(payload);
    expect(callbacks.onSetSetPlayed).toHaveBeenCalledWith({ player_id: 1, cards_played: [1, 2] });
    expect(callbacks.onNsfWindowOpen).toHaveBeenCalledWith(expect.objectContaining({
      actionId: 'a',
      rootActionId: 'a',
      playedBy: 1,
      playedByName: 'Bob',
      isCancellable: true,
      payload,
    }));
  });

  it('calls onSetDeckCount in handleDeckUpdated', () => {
    handlers.handleDeckUpdated({ size_deck: 5 }, 'INGAME');
    expect(callbacks.onSetDeckCount).toHaveBeenCalledWith(5);
  });

  it('calls onSetDraftCards with array in handleDraftUpdated', () => {
    handlers.handleDraftUpdated({ cards: [{ card_id: 1 }] }, 'INGAME');
    expect(callbacks.onSetDraftCards).toHaveBeenCalledWith([{ card_id: 1 }]);
  });

  it('calls onSetDraftCards with updater function in handleDraftUpdated', () => {
    const prevDraft = [{ card_id: 1 }, { card_id: 2 }];
    callbacks.onSetDraftCards.mockImplementation(fn => fn(prevDraft));
    handlers.handleDraftUpdated({ card_taken_id: 2, new_card: { card_id: 3 } }, 'INGAME');
    expect(callbacks.onSetDraftCards).toHaveBeenCalled();
    const result = callbacks.onSetDraftCards.mock.calls[0][0](prevDraft);
    expect(result).toEqual([{ card_id: 1 }, { card_id: 3, is_revealed: true }]);
  });

  it('calls onGameCancel in handleGameCancelled with LOBBY context', () => {
    handlers.handleGameCancelled({ game_id: 1 }, 'LOBBY');
    expect(callbacks.onGameCancel).toHaveBeenCalled();
  });

  it('calls onSetCurrentTurnId and onGameStartedLobby in handleGameStarted', () => {
    handlers.handleGameStarted({ first_player_id: 7 }, 'LOBBY');
    expect(callbacks.onSetCurrentTurnId).toHaveBeenCalledWith(7);
    expect(callbacks.onGameStartedLobby).toHaveBeenCalled();
  });

  it('calls onLobbyGameInfoUpdate in handleGameUpdated', () => {
    const payload = { GameLobbyInfo: { player_count: 2, max_players: 4, name: 'foo', game_id: 99 } };
    handlers.handleGameUpdated(payload, 'LOBBY');
    expect(callbacks.onLobbyGameInfoUpdate).toHaveBeenCalledWith(2, 4, 'foo', 99);
  });

  it('calls updateLobbyPlayers in handlePlayerJoined', () => {
    handlers.handlePlayerJoined({ player_name: 'A', game_id: 1 }, 'LOBBY');
    expect(callbacks.updateLobbyPlayers).toHaveBeenCalled();
  });

  it('calls onGameCancel in handlePlayerLeft if is_host', () => {
    handlers.handlePlayerLeft({ player_name: 'A', game_id: 1, is_host: true }, 'LOBBY');
    expect(callbacks.onGameCancel).toHaveBeenCalled();
  });

  it('calls updateLobbyPlayers in handlePlayerLeft if not host', () => {
    handlers.handlePlayerLeft({ player_name: 'A', game_id: 1, is_host: false }, 'LOBBY');
    expect(callbacks.updateLobbyPlayers).toHaveBeenCalled();
  });

  it('calls onPromptReveal in handlePromptReveal', () => {
    handlers.handlePromptReveal({}, 'INGAME');
    expect(callbacks.onPromptReveal).toHaveBeenCalledWith(true);
  });

  it('calls onPromptDrawFromDiscard in handlePromptDrawFromDiscard', () => {
    handlers.handlePromptDrawFromDiscard({ foo: 1 }, 'INGAME');
    expect(callbacks.onPromptDrawFromDiscard).toHaveBeenCalledWith({ foo: 1 });
  });

  it('calls onSecretRevealed and onGameOver if role=MURDERER in handleSecretRevealed', () => {
    handlers.handleSecretRevealed({ secret_id: 1, role: 'MURDERER', game_id: 2, player_id: 3 }, 'INGAME');
    expect(callbacks.onSecretRevealed).toHaveBeenCalledWith({ event: "SECRET_REVEALED", secret_id: 1, role: 'MURDERER', game_id: 2, player_id: 3 });
    expect(callbacks.onGameOver).toHaveBeenCalledWith({ event: "SECRET_REVEALED", role: 'MURDERER', player_id: 3 });
  });

  it('calls onSecretStolen in handleSecretStolen', () => {
    handlers.handleSecretStolen({ thief_id: 1, victim_id: 2 }, 'INGAME');
    expect(callbacks.onSecretStolen).toHaveBeenCalledWith(1, 2);
  });

  it('calls onSecretHidden in handleSecretHidden', () => {
    handlers.handleSecretHidden({ secret_id: 1, role: 'foo', game_id: 2, player_id: 3 }, 'INGAME');
    expect(callbacks.onSecretHidden).toHaveBeenCalledWith({ secret_id: 1, role: 'foo', game_id: 2, player_id: 3 });
  });

  it('calls onStolenSet in handleSetStolen', () => {
    handlers.handleSetStolen({ foo: 1 }, 'INGAME');
    expect(callbacks.onStolenSet).toHaveBeenCalledWith({ foo: 1 });
  });

  it('calls onCardsNSFDiscarded in handleCardsNSFDiscarded', () => {
    handlers.handleCardsNSFDiscarded({ source_player_id: 1, target_player_id: 2, discarded_cards: [1, 2] }, 'INGAME');
    expect(callbacks.onCardsNSFDiscarded).toHaveBeenCalledWith({
      source_player_id: 1,
      target_player_id: 2,
      discarded_cards: [1, 2],
      event: "CARDS_NSF_DISCARDED"
    });
  });

  it('calls onNsfWindowClose with CANCELLED in handleActionCancelled', () => {
    handlers.handleActionCancelled({ action_id: 'x' }, 'INGAME');
    expect(callbacks.onNsfWindowClose).toHaveBeenCalledWith({ actionId: 'x', status: "CANCELLED", payload: { action_id: 'x' } });
  });

  it('calls onSetSetPlayed and onNsfWindowClose with RESOLVED in handleActionResolved', () => {
    const payload = { action_id: 'y', player_id: 1, cards_resolved: [{ set_id: 2 }] };
    handlers.handleActionResolved(payload, 'INGAME');
    expect(callbacks.onSetSetPlayed).toHaveBeenCalledWith({ player_id: 1, cards_played: [{ set_id: 2 }] });
    expect(callbacks.onNsfWindowClose).toHaveBeenCalledWith({ actionId: 'y', status: "RESOLVED", payload });
  });

  it('calls onGameOver in handleGameOver', () => {
    handlers.handleGameOver({ foo: 1 }, 'INGAME');
    expect(callbacks.onGameOver).toHaveBeenCalledWith({ foo: 1 });
  });

  it('calls onVoteStarted in handleVoteStarted', () => {
    handlers.handleVoteStarted({ foo: 1 }, 'INGAME');
    expect(callbacks.onVoteStarted).toHaveBeenCalledWith({ foo: 1 });
  });

  it('calls onSocialDisgraceApplied in handleSocialDisgraceApplied', () => {
    handlers.handleSocialDisgraceApplied({ player_id: 1 }, 'INGAME');
    expect(callbacks.onSocialDisgraceApplied).toHaveBeenCalledWith(1);
  });

  it('calls onSocialDisgraceRemoved in handleSocialDisgraceRemoved', () => {
    handlers.handleSocialDisgraceRemoved({ player_id: 2 }, 'INGAME');
    expect(callbacks.onSocialDisgraceRemoved).toHaveBeenCalledWith(2);
  });
});