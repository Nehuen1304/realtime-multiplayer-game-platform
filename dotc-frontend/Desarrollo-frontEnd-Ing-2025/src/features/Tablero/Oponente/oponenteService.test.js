import { describe, it, expect, vi, beforeEach } from 'vitest';
import { obtenerManoOponente, obtenerSecretosOponente } from './oponenteService.js';

const mockResponse = (ok, jsonData, status = 200) => ({
  ok,
  status,
  json: vi.fn().mockResolvedValue(jsonData),
});

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('oponenteService', () => {
  it('obtenerManoOponente returns array on success', async () => {
    const hand = [{ id: 1 }];
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(mockResponse(true, hand));

    const res = await obtenerManoOponente(1, 2);
    expect(res).toEqual(hand);
    expect(global.fetch).toHaveBeenCalled();
    expect(global.fetch.mock.calls[0][0]).toMatch(/\/api\/games\/1\/players\/2\/hand$/);
  });

  it('obtenerManoOponente throws on error', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      mockResponse(false, { detail: 'boom' }, 500)
    );
    await expect(obtenerManoOponente(1, 2)).rejects.toThrow('boom');
  });

  it('obtenerSecretosOponente returns only secrets array', async () => {
    const payload = { secrets: [{ id: 7 }] };
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(mockResponse(true, payload));
    const res = await obtenerSecretosOponente(3, 4);
    expect(res).toEqual([{ id: 7 }]);
  });

  it('obtenerSecretosOponente throws with API error', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      mockResponse(false, { detail: 'nope' }, 404)
    );
    await expect(obtenerSecretosOponente(3, 4)).rejects.toThrow('nope');
  });
});
