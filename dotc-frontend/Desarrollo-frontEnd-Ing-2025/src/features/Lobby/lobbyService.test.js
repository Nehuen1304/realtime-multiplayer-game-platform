import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getGameState, startGame, cancelGame } from './lobbyService.js';

// Simple helper to build mock response
const mockResponse = (ok, jsonData, status = 200) => ({
  ok,
  status,
  json: vi.fn().mockResolvedValue(jsonData),
});

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('lobbyService', () => {
  it('getGameState returns parsed JSON on success', async () => {
    const data = { id: 1, players: [] };
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(mockResponse(true, data));

    const res = await getGameState(123);
    expect(res).toEqual(data);
    expect(global.fetch).toHaveBeenCalledTimes(1);
    // ensure URL constructed includes path
    expect(global.fetch.mock.calls[0][0]).toMatch(/\/api\/games\/123$/);
  });

  it('getGameState throws on non-ok', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(mockResponse(false, { detail: 'x' }, 500));
    await expect(getGameState(1)).rejects.toThrow(/No se pudo obtener/);
  });

  it('startGame posts with numeric ids and returns result', async () => {
    const payload = { ok: true };
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(mockResponse(true, payload));

    const res = await startGame('10', '20');
    expect(res).toEqual(payload);
    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toMatch(/\/api\/games\/10\/start$/);
    expect(options.method).toBe('POST');
    const body = JSON.parse(options.body);
    expect(body).toEqual({ player_id: 20, game_id: 10 });
  });

  it('startGame throws with backend detail on error', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      mockResponse(false, { detail: 'custom error' }, 400)
    );
    await expect(startGame(1, 2)).rejects.toThrow('custom error');
  });

  it('cancelGame posts and returns JSON on success', async () => {
    const payload = { ok: true };
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(mockResponse(true, payload));

    const res = await cancelGame(5, 6);
    expect(res).toEqual(payload);
    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toMatch(/\/api\/games\/5\/leave$/);
    expect(options.method).toBe('POST');
  });

  it('cancelGame throws with detail or default on error', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      // also test that .json() rejection is handled (catch -> {})
      {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error('bad json')),
      }
    );
    await expect(cancelGame(1, 2)).rejects.toThrow(/No se pudo abandonar/);
  });
});
