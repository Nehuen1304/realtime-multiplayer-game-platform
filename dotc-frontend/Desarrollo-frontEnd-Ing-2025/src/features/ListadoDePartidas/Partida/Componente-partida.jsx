
import './Componente-partida.css';
import { Button } from '../../../components/Button/Button'
import * as apiService from '../apiService.js';

export function PartidaLista({ idPartida, nombrePartida, jugadoresActuales, maxJugadores, playerId, onGameJoined, setAlerta }) {


	const datosParaUnirme = {
		player_id: playerId,
		game_id: idPartida,
	};

	const unirseLobby = async () => {
		try {
			
			const response = await apiService.unirsePartida(datosParaUnirme);
			console.log("se unio a la parida: ", response);
			if (onGameJoined) {
                onGameJoined(idPartida);
				console.log( 'playerId: '+playerId +'\n joined lobbyName: ' + nombrePartida +'\n idPartida:' +idPartida );
            }
		} catch (error) {
			
			if (setAlerta) {
                setAlerta({
                    titulo: "Error al Unirse",
                    mensaje: `No se pudo unir a la partida: ${error.message}`,
                    tipo: "error"
                })}
				else{
			alert(`Error al unirse la partida: ${error.message}`);
				}
		}
	}


	return (
		<div className="Componente-Partida">
			<section className="Partida-Nombre">
				<h1>{nombrePartida}</h1>
			</section>

			<div className="Partida-Derecha">

				<section className="Jugadores-En-Partida">
					<h2>{jugadoresActuales}/{maxJugadores}</h2>

				</section>

				<section>

					<Button variant='smallred' onClick={unirseLobby}>
						UNIRSE
					</Button>
				</section>
			</div>
		</div>
	);

}