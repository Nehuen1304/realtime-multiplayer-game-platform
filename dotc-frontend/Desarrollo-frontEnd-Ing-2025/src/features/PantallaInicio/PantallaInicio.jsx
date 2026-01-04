import React, { useState } from 'react';
import './PantallaInicio.css';
import logo from './logo_color.svg';
import { createPlayer } from './Service';
import { Input } from '../../components/Input/Input';
import { Window } from '../../components/Window/Window';
import { Button } from '../../components/Button/Button';

const PantallaInicio = ({ onPlayerCreated }) => {
	// manejar player ID, loading status y errores
	const [playerName, setPlayerName] = useState("");
	// const [playerId, setPlayerId] = useState(null);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState(null);
	const [birthDate, setBirthDate] = useState("");
	const nameEmpty = !playerName || playerName.trim() === "";

	// se llama a esta funcion cuando se cliquea el boton
	const handleJoinGame = async () => {
		setIsLoading(true); // Disable the button and show loading state
		setError(null);

		// Prepare the body data, use trimmed name to avoid leading/trailing spaces
		const trimmedName = playerName.trim();
		const requestData = {
			name: trimmedName,
			birth_date: birthDate // string in YYYY-MM-DD format
		};

		try {
			console.log(requestData);
			const data = await createPlayer(requestData);
			console.log(data);
			if (onPlayerCreated) {
				onPlayerCreated(trimmedName, data.player_id);
			}
		} catch (err) {
			setError(err?.message || 'No se pudo crear jugador');
			console.error(err);
		} finally {
			setIsLoading(false);
		}

	};

	return (
		<div className="pantalla-inicio-container">
			<img src={logo} className="pantalla-inicio-logo" alt="logo" />

			<Window title=''>
				<Input
					value={playerName}
					onChange={e => setPlayerName(e.target.value)}
					placeholder="Nombre del jugador"
					required={true}
				/>
				<Input
					type="date"
					value={birthDate}
					onChange={e => setBirthDate(e.target.value)}
					required={true}
				/>
				{error && <p style={{ color: 'black', marginTop: '1rem' }}>{error}</p>}
			</Window>
			<Button
				onClick={handleJoinGame}
				
				disabled={isLoading || nameEmpty || !birthDate}
				variant="primary"
				style={{ marginTop: '1rem' }}
			>
				{isLoading ? 'CARGANDO...' : 'JUGAR'}
			</Button>

		</div>
	);
};

export default PantallaInicio;