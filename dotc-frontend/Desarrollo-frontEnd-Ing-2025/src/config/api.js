/**
 * Configuración centralizada de la API.
 * USAR SIEMPRE esta URL en todos los servicios del frontend.
 * 
 * ⚠️ IMPORTANTE: Usar 'localhost' en lugar de '127.0.0.1' para evitar problemas de CORS.
 */
// La URL base del backend (SIN /api al final)
// Normalizar quitando una barra final si existe
export const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

/**
 * Construye una URL completa de API de forma segura.
 * Usa el constructor URL para evitar errores con paths complejos y '//' dobles.
 *
 * @param {string} path - El path del endpoint (ej: '/api/games', 'api/players')
 * @returns {string} La URL completa del endpoint
 */
export const getApiUrl = (path) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return new URL(normalizedPath, API_BASE_URL).toString();
};

/**
 * Genera la base para WebSockets a partir de la API base.
 * Mapea http->ws y https->wss de forma robusta.
 */
const _makeWebsocketBase = (base) => {
  try {
    const u = new URL(base);
    const wsProtocol = u.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${wsProtocol}//${u.host}${u.pathname.replace(/\/$/, '')}`;
  } catch (e) {
    return base.replace(/^http/, 'ws').replace(/\/$/, '');
  }
};

export const API_CONFIG = {
  // Permite que los tests de WS lo puedan mockear
  WEBSOCKET_BASE: (import.meta.env.VITE_WS_URL || API_BASE_URL.replace(/^http/i, 'ws')),
};
