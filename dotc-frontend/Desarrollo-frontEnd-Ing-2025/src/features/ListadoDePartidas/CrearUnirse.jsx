import { PartidaLista } from "./Partida/Componente-partida.jsx";
import { useEffect, useState, useRef, useMemo } from "react";
import { Formulario } from "./Formulario/Formulario.jsx";
import './CrearUnirse.css'
import '../PantallaInicio/PantallaInicio.css'
import logo from './logo_color.svg';
import { Button } from '../../components/Button/Button'
import { Input } from '../../components/Input/Input.jsx';
import * as apiService from './apiService.js';
import { Alerta } from "../../components/Alerta/Alerta.jsx";
import { normalizeWsMessage } from '../../ws/wsUtils.js';
import { API_CONFIG } from '../../config/api.js';

export function CrearUnirse({ playerName, playerId, onGameJoined }) {
	const [mostrandoFormulario, setMostrandoFormulario] = useState(false);

	//parar las listas
	const [partidas, setPartidas] = useState([]);
	const [cargandoPartidas, setCargandoPartidas] = useState(true);
	const [errorListado, setErrorListado] = useState(null);
	const [searchTerm, setSearchTerm] = useState('');
	const [alerta, setAlerta] = useState(null);
	const wsRef = useRef(null);

	const [partidaCreada, setPartidaCreada] = useState(false);
	const [errorCrearPartida, setErrorCrearPartida] = useState(false)

	const handleCrearPartida = async (datosPartida) => {
		try {
			setMostrandoFormulario(false);
			const response = await apiService.crearPartida(datosPartida);
			console.log(response);
			if (onGameJoined && response.game_id) {
				onGameJoined(response.game_id);
			}
			
			setTimeout(() => {
				setPartidaCreada(false);
			}, 5000); // Se resetea después de 5 segundos

		} catch (error) {
			setMostrandoFormulario(true);
			setPartidaCreada(false);
			setErrorCrearPartida(error.message);
			setAlerta({
				mensaje: "Error al crear la partida, Ya exite una partida con ese nombre ",
				tipo: "error"
			});
		}

	}
	/*--------------------------------------------------------------------------------------*/

	useEffect(() => {
		const cargarPartidas = async () => {
			try {
				setCargandoPartidas(true);
				const data = await apiService.obtenerPartidas();
				setPartidas(data.games || []);
				setErrorListado(null);
				// FIX: Reset the trigger after fetching so it can be used again.
				if (partidaCreada) {
					setPartidaCreada(false);
				}
			} catch (error) {
				setErrorListado(error.message);
				setAlerta({
					mensaje: "No se pudo obtener la lista de partidas ⚠️",
					tipo: "warning"
				});
				setPartidas([]);
			} finally {
				setCargandoPartidas(false);

			}
		};

		cargarPartidas();
	}, [partidaCreada]);

	// Suscribirse al canal global de main screen
	useEffect(() => {
        const ws = new WebSocket(`${API_CONFIG.WEBSOCKET_BASE}/ws/mainscreen`);
        wsRef.current = ws;

        ws.onmessage = (evt) => {
            const { event, payload } = normalizeWsMessage(evt.data);

            if (event === 'GAME_CREATED' || event === 'GAME_UPDATED') {
                const game = payload?.game ?? null;
                if (!game) return;
                // Agregar o actualizar sin duplicar (por id)
                setPartidas(prev => {
                    const exists = prev.some(p => p.id === game.id);
                    return exists
                        ? prev.map(p => (p.id === game.id ? { ...p, ...game } : p))
                        : [...prev, game];
                });
            }
        };
        ws.onerror = (e) => console.error('WS mainscreen error', e);
        ws.onclose = () => { /* opcional: reconexión si hace falta */ };
        return () => {
            try { ws.close(); } catch { }
            wsRef.current = null;
        };
    }, []);

	// Lista filtrada por busqueda y con cupo disponible
	const filteredPartidas = useMemo(() => {
		const term = searchTerm.trim().toLowerCase();
		return partidas.filter(p =>
			(!term || p.name?.toLowerCase().includes(term)) &&
			(p.player_count < p.max_players)
		);
	}, [partidas, searchTerm]);

	const renderListaDePartidas = () => {
		if (cargandoPartidas) return <p className="mensaje-feedback">Cargando partidas...</p>;
		if (errorListado) return <p className="error-message">Error: {errorListado}</p>;
		if (filteredPartidas.length === 0) return <p className="no-results-message">No se encontraron partidas.</p>;

		return filteredPartidas.map((partida) => (
			<PartidaLista
				key={partida.id} // ????
				playerId={playerId}
				onGameJoined={onGameJoined}
				idPartida={partida.id}
				nombrePartida={partida.name}
				jugadoresActuales={partida.player_count}
				maxJugadores={partida.max_players}
				setAlerta={setAlerta}
			/>
		));
	};
	const handleCancel = () => {
		setMostrandoFormulario(false);
		setPartidaCreada(false);
		setErrorCrearPartida(false);
	};

	const renderContent = () => {
		if (mostrandoFormulario) {
			return <Formulario playerId={playerId} onCreateGame={handleCrearPartida} cancelar={handleCancel} />;
		}

		if (partidaCreada) {
			return <h1>Se creó con éxito</h1>;
		}
		// if (errorCrearPartida) {
		// 	return <div className="error-message">{errorCrearPartida}</div>;
		// }
		return null;
	};

	return (
		<div className="pantalla-crear-unirse">
			<img src={logo} alt="Logo-Agatha" className="pantalla-inicio-logo" draggable={false} />
			{!mostrandoFormulario && !partidaCreada && !errorCrearPartida && (
				<Button onClick={() => setMostrandoFormulario(true)}>
					Crear Partida
				</Button>
			)}

			{/* Esta función ya se encarga de mostrar el formulario y otros estados */}
			{renderContent()}

			{/* Mostramos la lista de partidas solo si el formulario no está visible */}
			{!mostrandoFormulario && (
				<div className="Lista-partidas">
					<div className="search-container">
						<Input
							type="text"
							placeholder="Buscar partida por nombre..."
							value={searchTerm}
							onChange={(e) => setSearchTerm(e.target.value)}
						/>
					</div>

					<div className="games-scroll-container">
						{renderListaDePartidas()}
					</div>
				</div>
			)}

			{alerta && (
				<Alerta
					tipo={alerta.tipo}
					mensaje={alerta.mensaje}
					onClose={() => setAlerta(null)}
					duracion={3000}
				/>
			)}
		</div>
	);
}
