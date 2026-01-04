import { useEffect, useRef, useState } from 'react';
import { revelarSecreto } from '../ManoPropiaService.js';

/**
 * Maneja el flujo de "revelar secreto": banner, countdown y auto-reveal.
 */
export function useRevealSecretPrompt({
  revealSecretPrompt,
  secretCards,
  gameId,
  playerId,
  setRevealSecretPrompt,
  timeoutMs = 10000,
}) {
  const hasUnrevealedSecrets = secretCards?.some((s) => !s.is_revealed);
  const [showRevealHint, setShowRevealHint] = useState(false);
  const [revealCountdownMs, setRevealCountdownMs] = useState(timeoutMs);

  const intervalRef = useRef(null);
  const timerRef = useRef(null);
  const userSelectedSecretIdRef = useRef(null);

  const clearTimers = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (timerRef.current) clearTimeout(timerRef.current);
    intervalRef.current = null;
    timerRef.current = null;
  };

  const handleReveal = async (secretId) => {
    if (!gameId || !playerId || !secretId) return;
    try {
      userSelectedSecretIdRef.current = secretId;
      clearTimers();
      await revelarSecreto({ game_id: gameId, player_id: playerId, secret_id: secretId });
      setRevealSecretPrompt?.(false);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error('Error al revelar secreto:', e);
    }
  };

  useEffect(() => {
    // Reset cuando no hay prompt o no hay secretos por revelar
    if (!revealSecretPrompt || !hasUnrevealedSecrets) {
      setShowRevealHint(false);
      setRevealCountdownMs(timeoutMs);
      userSelectedSecretIdRef.current = null;
      clearTimers();
      return;
    }

    // Inicia banner + countdown + auto-reveal
    setShowRevealHint(true);
    setRevealCountdownMs(timeoutMs);

    clearTimers();
    intervalRef.current = setInterval(() => {
      setRevealCountdownMs((prev) => (prev > 100 ? prev - 100 : 0));
    }, 100);

    timerRef.current = setTimeout(() => {
      if (!userSelectedSecretIdRef.current) {
        const first = secretCards.find((s) => !s.is_revealed);
        if (first) handleReveal(first.secret_id);
      }
    }, timeoutMs);

    return clearTimers;
  }, [revealSecretPrompt, hasUnrevealedSecrets, secretCards, timeoutMs]);

  return {
    showRevealHint,
    revealCountdownMs,
    hasUnrevealedSecrets,
    handleReveal,
    timeoutMs,
  };
}
