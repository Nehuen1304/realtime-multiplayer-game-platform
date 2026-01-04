import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import * as tableroService from "./tableroService";

// Helper to mock fetch
function mockFetch(response, ok = true) {
  global.fetch = vi.fn().mockResolvedValue({
    ok,
    json: vi.fn().mockResolvedValue(response),
  });
}

describe("tableroService", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("getGameState", () => {
    it("fetches game state for a given gameId", async () => {
      const mockResponse = { detail: "ok", game: { id: 1, name: "test" } };
      mockFetch(mockResponse);

      const result = await tableroService.getGameState(1);
      expect(fetch).toHaveBeenCalledWith("http://localhost:8000/api/games/1", {});
      expect(result).toEqual(mockResponse);
    });

    it("throws error on API error", async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: vi.fn().mockResolvedValue({ detail: "Not found" }),
      });
      await expect(tableroService.getGameState(999)).rejects.toThrow("Not found");
    });
  });

  describe("getManoJugador", () => {
    it("fetches player hand", async () => {
      const mockResponse = { detail: "ok", cards: [{ card_id: 1 }] };
      mockFetch(mockResponse);

      const result = await tableroService.getManoJugador(1, 2);
      expect(fetch).toHaveBeenCalledWith("http://localhost:8000/api/games/1/players/2/hand", {});
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getDeckSize", () => {
    it("returns deck size as number", async () => {
      const mockResponse = { detail: "ok", size_deck: 42 };
      mockFetch(mockResponse);

      const result = await tableroService.getDeckSize(1);
      expect(fetch).toHaveBeenCalledWith("http://localhost:8000/api/games/1/size_deck", {});
      expect(result).toBe(42);
    });

    it("returns 0 if size_deck is not a number", async () => {
      const mockResponse = { detail: "ok", size_deck: "not-a-number" };
      mockFetch(mockResponse);

      const result = await tableroService.getDeckSize(1);
      expect(result).toBe(0);
    });
  });

  describe("drawCard", () => {
    it("calls draw endpoint with POST and body", async () => {
      const mockResponse = { detail: "ok", drawn_card: { card_id: 1 } };
      mockFetch(mockResponse);

      const sendb = { player_id: 2, game_id: 1, source: "deck" };
      const result = await tableroService.drawCard(1, sendb);

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/games/1/actions/draw",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(sendb),
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("drawDraftCard", () => {
    it("calls draw endpoint for draft card", async () => {
      const mockResponse = { detail: "ok", drawn_card: { card_id: 5 } };
      mockFetch(mockResponse);

      const result = await tableroService.drawDraftCard(1, 2, 5);

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/games/1/actions/draw",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            player_id: 2,
            game_id: 1,
            source: "draft",
            card_id: 5,
          }),
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("playCard", () => {
    it("calls play endpoint with POST and body", async () => {
      const mockResponse = { detail: "ok" };
      mockFetch(mockResponse);

      const sendb = {
        player_id: 2,
        game_id: 1,
        action_type: "PLAY_EVENT",
        card_ids: [10],
      };
      const result = await tableroService.playCard(1, sendb);

      expect(fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/games/1/actions/play",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(sendb),
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });
});