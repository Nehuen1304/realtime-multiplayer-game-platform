import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPlayer } from './Service.js';

const mockResponse = (ok, jsonData, status = 200) => ({
  ok,
  status,
  json: vi.fn().mockResolvedValue(jsonData),
});

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('PantallaInicio Service.createPlayer', () => {
  it('returns player_id on success', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      mockResponse(true, { player_id: 42 })
    );
    const result = await createPlayer({ name: 'Alice', key: 'abc' });
    expect(result).toEqual({ player_id: 42 });
    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toMatch(/\/api\/players$/);
    expect(options.method).toBe('POST');
    expect(JSON.parse(options.body)).toEqual({ name: 'Alice', key: 'abc' });
    expect(options.headers['Content-Type']).toBe('application/json');
  });

  it('throws friendly message when response is not ok', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(
      mockResponse(false, { err: true }, 400)
    );
    // Implementation catches non-ok and throws a friendly message
    await expect(createPlayer({})).rejects.toThrow(/Failed to connect to the game server/i);
  });

  it('throws a friendly error when fetch fails', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('network'));
    await expect(createPlayer({})).rejects.toThrow(/Failed to connect/);
  });
});
