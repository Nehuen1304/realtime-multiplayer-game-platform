import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Lobby } from './Lobby.jsx';

// Mock del servicio
vi.mock('./lobbyService', () => ({
  getGameState: vi.fn(),
  startGame: vi.fn(),
}));
const { getGameState, startGame } = await import('./lobbyService');

// Mock de WebSocket global
class MockWS {
  constructor(url) {
    this.url = url;
    this.onmessage = null;
    MockWS.instances.push(this);
  }
  send() { }
  close() { }
}
MockWS.instances = [];
beforeEach(() => {
  vi.stubGlobal('WebSocket', MockWS);
});
afterEach(() => {
  vi.unstubAllGlobals();
  MockWS.instances = [];
});

describe('Lobby', () => {
  beforeEach(() => {
    getGameState.mockResolvedValue({
      game: {
        name: 'Partida X',
        players: [
          { player_id: 1, player_name: 'Host' },
          { player_id: 2, player_name: 'Invitado' },
        ],
        host: { player_id: 1 },
      }
    });
    startGame.mockResolvedValue({});
  });

  it('renderiza nombre de partida y lista de jugadores', async () => {
    render(<Lobby gameId={123} playerId={2} onGameStarted={() => { }} />);
    await waitFor(() => {
      expect(screen.getByText('Partida X')).toBeInTheDocument();
    });
    expect(screen.getByText('Host')).toBeInTheDocument();
    expect(screen.getByText('Invitado')).toBeInTheDocument();
  });

  it('muestra botón INICIAR PARTIDA si el jugador es host', async () => {
    render(<Lobby gameId={123} playerId={1} onGameStarted={() => { }} />);
    await screen.findByText('Partida X');
    expect(screen.getByText('INICIAR PARTIDA')).toBeInTheDocument();
    expect(screen.queryByText(/Esperando a que el host/i)).not.toBeInTheDocument();
  });

  it('muestra mensaje de espera si no es host', async () => {
    render(<Lobby gameId={123} playerId={2} onGameStarted={() => { }} />);
    await screen.findByText('Partida X');
    expect(screen.getByText(/Esperando a que el host/i)).toBeInTheDocument();
    expect(screen.queryByText('INICIAR PARTIDA')).not.toBeInTheDocument();
  });

  it('al clickear INICIAR PARTIDA llama a startGame', async () => {
    render(<Lobby gameId={123} playerId={1} onGameStarted={() => { }} />);
    await screen.findByText('Partida X');
    fireEvent.click(screen.getByText('INICIAR PARTIDA'));
    expect(startGame).toHaveBeenCalledWith(123, 1);
  });

  it('reacciona al evento GAME_STARTED vía WebSocket', async () => {
    const onGameStarted = vi.fn();
    render(<Lobby gameId={123} playerId={2} onGameStarted={onGameStarted} />);
    await screen.findByText('Partida X');

    // Emitimos mensaje del WS
    const ws = MockWS.instances[0];
    ws.onmessage?.({ data: JSON.stringify({ event: 'GAME_STARTED' }) });

    await waitFor(() => {
      expect(onGameStarted).toHaveBeenCalledTimes(1);
    });
  });

  it('muestra (Host) al lado del nombre del host', async () => {
    render(<Lobby gameId={123} playerId={2} onGameStarted={() => { }} />);
    await screen.findByText('Partida X');
    const hostItem = screen.getByText('Host').closest('li');
    expect(hostItem).toHaveTextContent('Host');
    expect(hostItem).toHaveTextContent('(Host)');
    expect(hostItem).not.toHaveTextContent('(Tú)');
  });

  it('muestra (Tú) al lado del jugador actual', async () => {
    render(<Lobby gameId={123} playerId={2} onGameStarted={() => { }} />);
    await screen.findByText('Partida X');
    const youItem = screen.getByText('Invitado').closest('li');
    expect(youItem).toHaveTextContent('Invitado');
    expect(youItem).toHaveTextContent('(Tú)');
    expect(youItem).not.toHaveTextContent('(Host)');
  });

  it('muestra ambos (Host) y (Tú) si el host es el jugador actual', async () => {
    render(<Lobby gameId={123} playerId={1} onGameStarted={() => { }} />);
    await screen.findByText('Partida X');
    const hostYouItem = screen.getByText('Host').closest('li');
    expect(hostYouItem).toHaveTextContent('Host');
    expect(hostYouItem).toHaveTextContent('(Host)');
    expect(hostYouItem).toHaveTextContent('(Tú)');
  });

  it('no rompe si la lista de jugadores está vacía', async () => {
    getGameState.mockResolvedValueOnce({
      game: {
        name: 'Partida Vacía',
        players: [],
        host: { player_id: 1 },
      }
    });
    render(<Lobby gameId={999} playerId={1} onGameStarted={() => { }} />);
    await screen.findByText('Partida Vacía');
    expect(screen.queryByRole('listitem')).not.toBeInTheDocument();
  });

  it('no muestra nada si no hay game en la respuesta', async () => {
    getGameState.mockResolvedValueOnce({});
    render(<Lobby gameId={555} playerId={1} onGameStarted={() => { }} />);
    // No debería romper ni renderizar jugadores
    await waitFor(() => {
      expect(screen.queryByText('INICIAR PARTIDA')).not.toBeInTheDocument();
    });
  });

  it('muestra alert si startGame falla', async () => {
    startGame.mockRejectedValueOnce(new Error('fail'));
    render(<Lobby gameId={123} playerId={1} onGameStarted={() => { }} />);
    await screen.findByText('Partida X');
    fireEvent.click(screen.getByText('INICIAR PARTIDA'));
    await waitFor(() => {
      // Se muestra la Alerta con el mensaje de error
      expect(screen.getByText('No se pudo iniciar la partida')).toBeInTheDocument();
    });
  });
});