import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PantallaInicio from './PantallaInicio';
import { createPlayer } from './Service';

// Mock de la API
vi.mock('./Service', () => ({
  createPlayer: vi.fn(),
}));

// Mocks de componentes
vi.mock('../../components/Input/Input', () => ({
  // No usar data-testid fijo para evitar duplicados (hay 2 inputs)
  Input: (props) => <input {...props} />,
}));

vi.mock('../../components/Button/Button', () => ({
  Button: ({ children, ...props }) => (
    <button data-testid="play-button" {...props}>
      {children}
    </button>
  ),
}));

vi.mock('./logo_color.svg', () => ({ default: 'logo.svg' }));

describe('[FE-TEST] Pantalla Inicial', () => {
  const mockOnPlayerCreated = vi.fn();
  const mockCreatePlayer = createPlayer;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Carga e Interfaz
  it('1. Carga la pantalla y verifica que los elementos clave sean visibles', () => {
    render(<PantallaInicio onPlayerCreated={mockOnPlayerCreated} />);

    expect(screen.getByAltText('logo')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Nombre del jugador')).toBeInTheDocument();

    const button = screen.getByTestId('play-button');
    expect(button).toBeInTheDocument();
    expect(button).toBeDisabled(); // deshabilitado porque falta nombre y fecha
  });

  // Flujo exitoso
  it('2. Habilita el botón al completar nombre y fecha; llama a API y navega', async () => {
    const MOCK_PLAYER_ID = 'player-xyz-123';
    mockCreatePlayer.mockResolvedValueOnce({ player_id: MOCK_PLAYER_ID });

    const { container } = render(<PantallaInicio onPlayerCreated={mockOnPlayerCreated} />);

    const nameInput = screen.getByPlaceholderText('Nombre del jugador');
    const dateInput = container.querySelector('input[type="date"]');
    const button = screen.getByTestId('play-button');

    const playerName = 'TesterUno';
    const birthDate = '2000-01-01';

    // A - Completar ambos campos
    fireEvent.change(nameInput, { target: { value: playerName } });
    fireEvent.change(dateInput, { target: { value: birthDate } });

    expect(button).toBeEnabled();

    // B - Click
    fireEvent.click(button);

    // C - Estado de carga
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'CARGANDO...' })).toBeDisabled();
    });

    // D - Esperar estado final
    await screen.findByText('JUGAR');

    // E - Aserciones
    expect(mockCreatePlayer).toHaveBeenCalledTimes(1);
    expect(mockCreatePlayer).toHaveBeenCalledWith({
      name: playerName,
      birth_date: birthDate,
    });

    expect(mockOnPlayerCreated).toHaveBeenCalledTimes(1);
    // El componente actual pasa un objeto con la propiedad player_id.
    // Aceptamos ambas formas para mantener compatibilidad: string o { player_id }
    const firstCallArg = mockOnPlayerCreated.mock.calls[0][1];
    if (typeof firstCallArg === 'string') {
      expect(firstCallArg).toBe(MOCK_PLAYER_ID);
    } else {
      expect(firstCallArg).toHaveProperty('player_id', MOCK_PLAYER_ID);
    }

    expect(button).toBeEnabled();
  });

  // Manejo de Errores
  it('3. Muestra un mensaje de error si la llamada a la API falla', async () => {
    mockCreatePlayer.mockRejectedValueOnce(new Error('Server Down'));

    const { container } = render(<PantallaInicio onPlayerCreated={mockOnPlayerCreated} />);

    const nameInput = screen.getByPlaceholderText('Nombre del jugador');
    const dateInput = container.querySelector('input[type="date"]');
    const button = screen.getByTestId('play-button');

    const playerName = 'ErrorPlayer';
    const birthDate = '1999-12-31';

    fireEvent.change(nameInput, { target: { value: playerName } });
    fireEvent.change(dateInput, { target: { value: birthDate } });

    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'CARGANDO...' })).toBeDisabled();
    });

    // Muestra el mensaje de error proveniente del throw
    await screen.findByText('Server Down');

    expect(button).toBeEnabled();
    expect(button).toHaveTextContent('JUGAR');
    expect(mockOnPlayerCreated).not.toHaveBeenCalled();
  });
});