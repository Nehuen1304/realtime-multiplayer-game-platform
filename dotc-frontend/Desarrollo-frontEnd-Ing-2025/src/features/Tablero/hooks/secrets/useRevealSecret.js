import { useCallback, useEffect, useState } from 'react';

// Maneja el evento de revelar secreto y sincroniza el estado local de secretos del jugador
export function useRevealSecret({ playerId, setSecretP, updateOpponentSecrets }) {
	const [revealedSecret, setRevealedSecret] = useState({});
	const [hiddenSecret, setHiddenSecret] = useState({});

	const onSecretRevealed = useCallback((payload) => {
		setRevealedSecret(payload || {});
	}, []);

	const onSecretHidden = useCallback((payload) => {
		setHiddenSecret(payload || {});
	}, []);

	useEffect(() => {
		if (!revealedSecret?.secret_id) return;

		if (Number(revealedSecret.player_id) === Number(playerId)) {
			setSecretP(prev => {
				if (!prev) return prev;
				if (Array.isArray(prev)) {
					return prev.map(s =>
						Number(s.secret_id) === Number(revealedSecret.secret_id)
							? { ...s, is_revealed: true }
							: s
					);
				}
				return prev;
			});
		} else {
			const pid = revealedSecret.player_id;
			updateOpponentSecrets(pid, (curr = []) =>
				(curr ?? []).map(s =>
					Number(s.secret_id) === Number(revealedSecret.secret_id)
						? { ...s, is_revealed: true }
						: s
				)
			);
		}

		// Limpiar el estado después de procesar
		setRevealedSecret({});

	}, [revealedSecret]);

	useEffect(() => {
		if (!hiddenSecret?.secret_id) return;
		if (Number(hiddenSecret.player_id) === Number(playerId)) {
			console.log('hiddenSecret PROPIO, hiddenSecret:', hiddenSecret);
			setSecretP(prev => {
				if (!prev) return prev;
				if (Array.isArray(prev)) {
					return prev.map(s =>
						Number(s.secret_id) === Number(hiddenSecret.secret_id)
							? { ...s, is_revealed: false }
							: s
					);
				}
				return prev;
			});
		}
		else {
			console.log('hiddenSecret AJENO, hiddenSecret:', hiddenSecret);
			const pid = hiddenSecret.player_id;
			updateOpponentSecrets(pid, (curr = []) =>
				(curr ?? []).map(s =>
					Number(s.secret_id) === Number(hiddenSecret.secret_id)
						? { ...s, is_revealed: false }
						: s
				)
			);
		}

		// Limpiar el estado después de procesar
		setHiddenSecret({});
		
	}, [hiddenSecret]);

	return { revealedSecret, onSecretRevealed, onSecretHidden };
}
