# 📖 Documentación de la API de WebSockets

Esta es la lista de todos los posibles eventos que el servidor puede enviar a través de WebSockets.

La estructura general de cada mensaje es:
```json
{
  "details": { ...payload... }
}
```

<br>

--- 

## Evento: `ACTION_CANCELLED`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que la acción de un jugador ha sido cancelada.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `player_id` | `int` | ID del jugador cuya acción fue cancelada. | Sí |
| `cards_cancelled` | `List[Card]` | Las cartas involucradas en la acción cancelada. | Sí |

--- 

## Evento: `ACTION_RESOLVED`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que la acción de un jugador ha sido resuelta.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `player_id` | `int` | ID del jugador cuya acción fue resuelta. | Sí |
| `cards_resolved` | `List[Card]` | Las cartas involucradas en la acción resuelta. | Sí |

--- 

## Evento: `CARDS_NSF_DISCARDED`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que un jugador ha obligado a otro a descartar todas sus cartas de tipo 'Not So Fast'.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `source_player_id` | `int` | ID del jugador que obligó a descartar cartas. | Sí |
| `target_player_id` | `int` | ID del jugador que fue obligado a descartar cartas. | Sí |
| `discarded_cards` | `List[Card]` | Las cartas de tipo 'Not So Fast' que fueron descartadas. | Sí |

--- 

## Evento: `CARDS_PLAYED`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que un jugador ha jugado un conjunto de cartas (para formar un set).

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `player_id` | `int` | ID del jugador que jugó las cartas. | Sí |
| `cards_played` | `List[Card]` | Las cartas que fueron jugadas. | Sí |
| `is_cancellable` | `bool` |   | Sí |
| `player_name` | `Optional[str]` |   | No |

--- 

## Evento: `CARD_DISCARDED`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que un jugador ha descartado una carta.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `player_id` | `int` | ID del jugador que descartó la carta. | Sí |
| `card` | `Card` | La carta que fue descartada. | Sí |

--- 

## Evento: `CARD_PLAYED`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que un jugador ha jugado una carta.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `player_id` | `int` | ID del jugador que jugó la carta. | Sí |
| `card_played` | `Card` | La carta que fue jugada. | Sí |

--- 

## Evento: `DECK_UPDATED`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Evento genérico para forzar una actualización del estado del mazo en los clientes.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `deck_size` | `int` | El tamaño actual del mazo de robo. | Sí |

--- 

## Evento: `DRAFT_UPDATED`

**Descripción:** Notifica que un slot del Card Draft ha sido actualizado.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `card_taken_id` | `int` |   | Sí |
| `new_card` | `Optional[Card]` |   | No |

--- 

## Evento: `GAME_CANCELLED`

**Descripción:** Destinatarios: Broadcast a todos en el Lobby. Notifica que una partida fue cancelada y ya no está disponible.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `game_id` | `int` | ID de la partida que fue eliminada. | Sí |

--- 

## Evento: `GAME_CREATED`

**Descripción:** Destinatarios: Broadcast a todos en el Lobby. Notifica que una nueva partida está disponible para unirse.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `game` | `GameLobbyInfo` | Objeto con la información pública de la nueva partida. | Sí |

--- 

## Evento: `GAME_OVER`

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `game_id` | `int` | Partida finalizada | Sí |

--- 

## Evento: `GAME_STARTED`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Anuncia que el juego ha comenzado. Este evento va acompañado de un 'GAME_UPDATED' al lobby para cambiar el estado de la partida.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `game_id` | `int` | ID de la partida que ha comenzado. | Sí |
| `players_in_turn_order` | `List[int]` | Lista de IDs de los jugadores en su orden de turno. | Sí |
| `first_player_id` | `int` | ID del jugador que tiene el primer turno. | Sí |

--- 

## Evento: `GAME_UPDATED`

**Descripción:** Destinatarios: Broadcast a todos en el Lobby. Actualiza la información de una partida existente en el Lobby (ej: contador de jugadores, estado).

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `game` | `GameLobbyInfo` | El objeto completo y actualizado de la partida en el lobby. | Sí |

--- 

## Evento: `HAND_UPDATED`

**Descripción:** Destinatarios: Mensaje privado a un jugador específico. Notifica que su mano ha sido actualizada.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `hand` | `List[Card]` | La mano actualizada del jugador. | Sí |

--- 

## Evento: `NEW_TURN`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Anuncia el inicio de un nuevo turno.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `turn_player_id` | `int` | ID del jugador que ahora tiene el turno. | Sí |

--- 

## Evento: `PLAYER_DREW_FROM_DECK`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica públicamente que un jugador ha robado del mazo (sin revelar la carta).

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `player_id` | `int` | ID del jugador que robó la carta. | Sí |
| `deck_size` | `int` | El nuevo tamaño del mazo de robo tras la acción. | Sí |

--- 

## Evento: `PLAYER_JOINED`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que un nuevo jugador se ha unido al juego. Este evento va acompañado de un 'GAME_UPDATED' al lobby.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `player_id` | `int` | ID del jugador que se unió. | Sí |
| `player_name` | `str` | Nombre del jugador que se unió. | Sí |
| `game_id` | `int` | ID de la partida a la que se unió. | Sí |

--- 

## Evento: `PLAYER_LEFT`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que un jugador ha abandonado el juego. Este evento va acompañado de un 'GAME_UPDATED' al lobby.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `player_id` | `int` | ID del jugador que abandonó la partida. | Sí |
| `player_name` | `str` | Nombre del jugador que se fue. | Sí |
| `game_id` | `int` | ID de la partida que abandonó. | Sí |
| `is_host` | `bool` | Indica si el jugador que se fue era el anfitrión (host). | No |

--- 

## Evento: `PROMPT_DRAW_FROM_DISCARD`

**Descripción:** Destinatarios: Un jugador en ESPECIFICO pidiendole que seleccione una carta de las mostradas para robar a su mano.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `cards` | `List[Card]` | Tenes que elegir una carta de las ultimas en la pila de descarte. | Sí |

--- 

## Evento: `PROMPT_REVEAL`

**Descripción:** Destinatarios: Mensaje privado a un jugador específico. Le ordena al jugador que debe elegir un secreto para revelar.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|

--- 

## Evento: `REQUEST_TO_DONATE`

**Descripción:** Destinatarios: Broadcast a todos en el lobby. Notifica que "tienes que donar una carta al jugador de {direction = [ left right ]}

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `direction` | `Literal` | La dirección a la que se debe donar la carta. | Sí |

--- 

## Evento: `SD_APPLIED`

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `player_id` | `int` | Jugador afectado | Sí |
| `game_id` | `int` | Partida | Sí |

--- 

## Evento: `SD_REMOVED`

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `player_id` | `int` | Jugador afectado | Sí |
| `game_id` | `int` | Partida | Sí |

--- 

## Evento: `SECRET_HIDDEN`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que un secreto de un jugador fue ocultado.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `secret_id` | `int` | Secreto ocultado | Sí |
| `player_id` | `int` | ID del jugador dueño del secreto | Sí |
| `game_id` | `int` | ID de la partida a la que se unió. | Sí |

--- 

## Evento: `SECRET_REVEALED`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que el secreto de un jugador ha sido revelado.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `secret_id` | `int` | Secreto a revelar | Sí |
| `role` | `PlayerRole` | ROL | Sí |
| `game_id` | `int` | ID de la partida a la que se unió. | Sí |
| `player_id` | `int` | dueno del secreto | Sí |

--- 

## Evento: `SECRET_STOLEN`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que un secreto fue robado de un jugador y transferido a otro.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `thief_id` | `int` | ID del jugador que ahora posee el secreto. | Sí |
| `victim_id` | `int` | ID del jugador que perdió el secreto. | Sí |

--- 

## Evento: `SET_STOLEN`

**Descripción:** Destinatarios: Broadcast a los jugadores de la partida. Notifica que un set ha sido robado de un jugador y transferido a otro.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `thief_id` | `int` | ID del jugador que ahora posee el set. | Sí |
| `victim_id` | `int` | ID del jugador que perdió el set. | Sí |
| `set_id` | `int` | ID del set que fue robado. | Sí |
| `set_cards` | `List[Card]` | Las cartas que componen el set robado. | Sí |

--- 

## Evento: `TRADE_REQUESTED`

**Descripción:** Destinatarios: Mensaje privado a un jugador específico. Notifica que debe seleccionar una carta para intercambiar.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `initiator_player_id` | `int` | ID del jugador que inició el intercambio. | Sí |

--- 

## Evento: `VOTE_ENDED`

**Descripción:** Payload para cuando una votación ha terminado.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|
| `most_voted_player_id` | `Optional[int]` |   | Sí |
| `tie` | `bool` |   | Sí |

--- 

## Evento: `VOTE_STARTED`

**Descripción:** Payload para cuando se inicia una votación. El payload está vacío, la llegada del evento es la señal.

**Payload (`details`):**

| Campo | Tipo | Descripción | Requerido |
|---|---|---|---|

