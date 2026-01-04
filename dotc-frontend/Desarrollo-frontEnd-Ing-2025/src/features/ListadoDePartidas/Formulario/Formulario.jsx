
import { useEffect, useState } from 'react';
import './Form.css'
import { Button } from '../../../components/Button/Button'
import { Input } from '../../../components/Input/Input.jsx';
import { Window } from '../../../components/Window/Window.jsx';
import { Slider } from '@mui/material';

export function Formulario({ onCreateGame, cancelar, playerId }) {
	const [nombrePartida, setNombrePartida] = useState('');
	const [playerRange, setPlayerRange] = useState([2, 6]);
	const [error, setError] = useState(null);
	const nameEmpty = !nombrePartida || nombrePartida.trim() === '';

	// const nuevoJugador = 0;

	const minJugadores = playerRange[0];
	const maxJugadores = playerRange[1];

	useEffect(() => {
		if (maxJugadores < minJugadores) {
			setError("La minima cantidad de jugadores esta superando el maximo");
		} else {
			setError(null);
		}
	}, [playerRange]);


	const handleSubmit = (event) => {
		event.preventDefault();


		if (error) {
			console.log("Error al validar los datos ingresados por favor ingrese nuevamente");
			return;
		}

		const datosPartida = {
			host_id: playerId,
			game_name: nombrePartida,
			min_players: parseInt(minJugadores),
			max_players: parseInt(maxJugadores)
		};

		onCreateGame(datosPartida);
	};
	return (
		//*Usamos sumbit para poder recuperar los elemetos del formulario 
		<form onSubmit={handleSubmit} >

			<div className="total-creacion">

				<Window> {/*ventana formulario creacion partida*/}

					<Input
						type="text"
						id="nombre"
						placeholder="Nombre de la Partida"
						value={nombrePartida}
						required
						onChange={(e) => setNombrePartida(e.target.value)}
					/>

					{/* Slider component from rc-slider */}
					<div className='rango'>
						<h2>
							Rango de Jugadores
						</h2>
						<Slider
							color='secondary'
							value={playerRange}
							onChange={(e, newValue) => setPlayerRange(newValue)}
							valueLabelDisplay="auto"
							min={2}
							max={6}
							step={1}
							marks={[
								{ value: 2, label: '2' },
								{ value: 3, label: '3' },
								{ value: 4, label: '4' },
								{ value: 5, label: '5' },
								{ value: 6, label: '6' },
							]}
							disableSwap
							sx={{
								color: '#c73737',
								fontFamily: 'Raleway, sans-serif',
								height: 8,
								'& .MuiSlider-thumb': {
									backgroundColor: '#c73737',
									border: '2px solid #c73737',
								},
								'& .MuiSlider-rail': {
									backgroundColor: '#000000ff',
								},
								'& .MuiSlider-markLabel': {
									color: '#000000ff',
									fontWeight: 'bold',
									fontFamily: 'Raleway, sans-serif',
								},
								'& .MuiSlider-valueLabel': {
									fontFamily: 'Raleway, sans-serif',
									color: '#ffffffff',
									fontWeight: 'bold',
								},
							}}
						/>
					</div>
						

					<Button variant='inverted' type="submit" disabled={nameEmpty || error}>
						CREAR PARTIDA
					</Button>


				</Window>

				<Button variant='cancel' type="button" onClick={cancelar}>
					CANCELAR
				</Button>

			</div>


			{error && (<div className="error-message">
				{error}
			</div>)

			}



		</form>
	);
}