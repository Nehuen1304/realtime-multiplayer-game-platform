# Death on the Cards (Web Adaptation)

Web adaptation of the card game “Agatha Christie – Death on the Cards”. Built for the browser with responsive layout and mobile touch support.

- Frontend: React + Vite
- Interaction: mouse and touch gestures (tap, long-press)
- UI: optimized for desktop and mobile, with card animations and dynamic opponent layout
- Game flow: lobby, board, own hand, detective sets, events, and endgame

## Development
- Install dependencies: `npm install`
- Run dev server: `npm run dev`
- Tests: `npm run test`

## Notes
- Uses WebSocket for real-time state
- Supports special events (Not So Fast, card swap, reveal/hide secrets)
- Includes played-cards modal and game-over screen


# Death on the Cards (Adaptación Web)

Adaptación web del juego de cartas “Agatha Christie – Death on the Cards”. Pensado para jugar en navegador, con soporte responsive y pantallas táctiles (mobile).

- Frontend: React + Vite.
- Interacción: compatible con mouse y gestos táctiles (tap, long-press).
- UI: optimizada para escritorio y móviles, con animaciones de cartas y disposición dinámica de oponentes.
- Estados de juego: lobby, tablero, mano propia, sets de detective, eventos y fin de partida.

## Desarrollo
- Instalar dependencias: `npm install`
- Ejecutar en desarrollo: `npm run dev`
- Pruebas: `npm run test`

## Notas
- Integra WebSocket para estado en tiempo real.
- Soporta eventos especiales (Not So Fast, intercambio de cartas, revelar/ocultar secretos).
- Incluye modal de cartas jugadas y pantalla de fin de juego.