import { useState, useCallback } from 'react';

export function useSocialDisgrace(playerId) {
  const [sdPlayers, setSdPlayers] = useState(() => new Set());

  const markSD = useCallback((pid) => {
    setSdPlayers(prev => {
      const next = new Set(prev);
      next.add(Number(pid));
      return next;
    });
  }, []);

  const clearSD = useCallback((pid) => {
    setSdPlayers(prev => {
      const next = new Set(prev);
      next.delete(Number(pid));
      return next;
    });
  }, [playerId]);

  const hasSocialDisgrace = sdPlayers.has(playerId);

  return { sdPlayers, markSD, clearSD, hasSocialDisgrace };
}