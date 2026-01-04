// src/features/ListadoDePartidas/CrearUnirse.test.jsx

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CrearUnirse } from './CrearUnirse';
import * as apiService from './apiService.js';

// 1. Mockear el módulo completo de apiService
vi.mock('./apiService.js');

// Mock del logo para evitar errores de importación en el test
vi.mock('./logo_color.svg', () => ({ default: 'logo.svg' }));

describe('[FE-TEST] Pantalla Crear o Unirse a Partida', () => {
    // Mocks para las props que necesita el componente
    const mockOnGameJoined = vi.fn();
    const mockPlayerId = 1;
    const mockPlayerName = 'Tester';

    // Resetear los mocks antes de cada test para asegurar que estén limpios
    beforeEach(() => {
        vi.clearAllMocks();
    });

    /**
     * SUITE DE TESTS 1: LISTADO DE PARTIDAS (GET /api/games)
     */
    describe('1. Pruebas de Listado de Partidas (GET)', () => {
        it('1.1. Muestra el estado de "Cargando partidas..." inicialmente', async () => {
            // Arrange: Simulamos que la API tarda en responder
            apiService.obtenerPartidas.mockReturnValue(new Promise(() => {}));
            
            // Act
            render(<CrearUnirse playerId={mockPlayerId} playerName={mockPlayerName} onGameJoined={mockOnGameJoined} />);

            // Assert
            expect(screen.getByText('Cargando partidas...')).toBeInTheDocument();
        });

        it('1.2. Renderiza la lista de partidas si la API responde con datos', async () => {
            // Arrange: Mock de una respuesta exitosa con 2 partidas
            const mockGames = {
                games: [
                    { id: 1, name: 'Partida de Valientes', player_count: 3, max_players: 6 },
                    { id: 2, name: 'Sala de Pruebas', player_count: 1, max_players: 4 },
                ],
            };
            apiService.obtenerPartidas.mockResolvedValue(mockGames);

            // Act
            render(<CrearUnirse playerId={mockPlayerId} playerName={mockPlayerName} onGameJoined={mockOnGameJoined} />);

            // Assert
            // Esperamos a que aparezcan los nombres de las partidas
            expect(await screen.findByText('Partida de Valientes')).toBeInTheDocument();
            expect(screen.getByText('Sala de Pruebas')).toBeInTheDocument();
            // Verificamos que el mensaje de carga ya no esté
            expect(screen.queryByText('Cargando partidas...')).toBeNull();
        });

        it('1.3. Muestra un mensaje si no hay partidas disponibles', async () => {
            // Arrange: Mock de una respuesta exitosa pero vacia
            apiService.obtenerPartidas.mockResolvedValue({ games: [] });

            // Act
            render(<CrearUnirse playerId={mockPlayerId} playerName={mockPlayerName} onGameJoined={mockOnGameJoined} />);
            
            // Assert
            expect(await screen.findByText('No se encontraron partidas.')).toBeInTheDocument();
        });

        it('1.4. Muestra un mensaje de error si la petición GET falla', async () => {
            // Arrange: Mock de un error en la API
            const errorMessage = 'Error de conexión con el servidor';
            apiService.obtenerPartidas.mockRejectedValue(new Error(errorMessage));

            // Act
            render(<CrearUnirse playerId={mockPlayerId} playerName={mockPlayerName} onGameJoined={mockOnGameJoined} />);

            // Assert
            expect(await screen.findByText(`Error: ${errorMessage}`)).toBeInTheDocument();
        });
    });

    /**
     * SUITE DE TESTS 2: CREACIÓN DE PARTIDA (POST /api/games)
     */
    describe('2. Pruebas de Creación de Partida (POST)', () => {
        beforeEach(() => {
            // Para los tests de creacion, asumimos que la carga inicial de partidas fue exitosa y vacia
            apiService.obtenerPartidas.mockResolvedValue({ games: [] });
        });

        it('2.1. El campo "Nombre de la Partida" en el formulario es obligatorio', async () => {
            // Act
            render(<CrearUnirse playerId={mockPlayerId} playerName={mockPlayerName} onGameJoined={mockOnGameJoined} />);
            
            // Hacemos click para abrir el formulario
            fireEvent.click(screen.getByRole('button', { name: /Crear Partida/i }));

            // Assert
            // El HTML valida esto con el atributo 'required'
            expect(await screen.findByPlaceholderText('Nombre de la Partida')).toBeRequired();
        });
        
        it('2.2. Crea una partida y llama a onGameJoined tras una respuesta 201 Created', async () => {
            // Arrange
            const newGameId = 3;
            const newGameName = 'Mi Partida';
            apiService.crearPartida.mockResolvedValue({ game_id: newGameId });
            
            // Act
            render(<CrearUnirse playerId={mockPlayerId} playerName={mockPlayerName} onGameJoined={mockOnGameJoined} />);
            fireEvent.click(screen.getByRole('button', { name: /Crear Partida/i }));

            // Llenamos el formulario
            const inputNombre = await screen.findByPlaceholderText('Nombre de la Partida');
            const submitButton = screen.getByRole('button', { name: 'CREAR PARTIDA' });

            fireEvent.change(inputNombre, { target: { value: newGameName } });
            fireEvent.click(submitButton);

            // Assert
            // Esperamos a que la función mock de la API haya sido llamada
            await waitFor(() => {
                expect(apiService.crearPartida).toHaveBeenCalledTimes(1);
            });

            // Verificamos que se llamo con los datos correctos (valores por defecto del slider)
            expect(apiService.crearPartida).toHaveBeenCalledWith({
                host_id: mockPlayerId,
                game_name: newGameName,
                min_players: 2,
                max_players: 6,
            });

            // Verificamos que se llamo a la función de "redireccion"
            expect(mockOnGameJoined).toHaveBeenCalledWith(newGameId);
        });
    });

    /**
     * SUITE DE TESTS 3: UNIRSE A PARTIDA (Desde la lista)
     */
    describe('3. Pruebas de Unión a Partida', () => {
        it('3.1. Se une a una partida existente y llama a onGameJoined', async () => {
             // Arrange
            const mockGames = {
                games: [{ id: 1, name: 'Partida de Valientes', player_count: 3, max_players: 6 }],
            };
            apiService.obtenerPartidas.mockResolvedValue(mockGames);
            apiService.unirsePartida.mockResolvedValue({ message: 'Player joined successfully' });

            // Act
            render(<CrearUnirse playerId={mockPlayerId} playerName={mockPlayerName} onGameJoined={mockOnGameJoined} />);
            const joinButton = await screen.findByRole('button', { name: /UNIRSE/i });
            fireEvent.click(joinButton);

            // Assert
            await waitFor(() => {
                expect(apiService.unirsePartida).toHaveBeenCalledTimes(1);
            });
            expect(apiService.unirsePartida).toHaveBeenCalledWith({
                player_id: mockPlayerId,
                game_id: 1,
            });
            expect(mockOnGameJoined).toHaveBeenCalledWith(1);
        });
    });
});