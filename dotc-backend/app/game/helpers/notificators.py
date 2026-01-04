from typing import List, Optional, Literal

# Dependencia de la interfaz, no de la implementación concreta
from ...websockets.interfaces import IConnectionManager

# Importa todos los modelos de detalles que vamos a usar
from ...websockets.protocol import details

# El modelo principal que envuelve todos los mensajes
from ...websockets.protocol.messages import WSMessage

# Modelos de dominio y DTOs que necesita el notificator
from ...domain.models import Card, PlayerInGame
from ...domain.enums import PlayerRole

from ...api.schemas import GameLobbyInfo


class Notificator:
    """
    Servicio para construir y enviar notificaciones de negocio estandarizadas.
    Está completamente desacoplado del formato de transmisión (JSON)
    y de la implementación del WebSocket Manager.
    """

    def __init__(self, ws_manager: IConnectionManager):
        self.manager = ws_manager

    # --- Métodos para notificar al Lobby (Broadcast to Lobby) ---

    async def notify_game_created(self, game: GameLobbyInfo):
        """Notifica al lobby que se ha creado una nueva partida."""
        details_model = details.GameCreatedDetails(game=game)
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_lobby(message)

    async def notify_game_removed(self, game_id: int):
        """Notifica al lobby que una partida ha sido cancelada/eliminada."""
        details_model = details.GameRemovedDetails(game_id=game_id)
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_lobby(message)

    # --- Métodos para notificar a una Partida (Broadcast to Game) ---

    async def notify_murderer_wins(self, game_id: int,
                                    murderer_id: int,
                                    accomplice_id: Optional[int]):
        """Notifica a todos en la partida que el asesino ha ganado."""
        details_model = details.GameOverDetails(
            reason="MURDERER_WIN",
            murderer_id=murderer_id,
            accomplice_id=accomplice_id,
            game_id=game_id)
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_innocents_win(self, game_id: int,
                                    murderer_id: int,
                                    accomplice_id: Optional[int]):
        """Notifica a todos en la partida que los inocentes han ganado."""
        details_model = details.GameOverDetails(
            reason="INNOCENTS_WIN",
            murderer_id=murderer_id,
            accomplice_id=accomplice_id,
            game_id=game_id)
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_new_turn(self, game_id: int, turn_player_id: int):
        """Notifica a todos en la partida el inicio de un nuevo turno."""
        details_model = details.NewTurnDetails(turn_player_id=turn_player_id)
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_card_played(
        self, game_id: int, player_id: int, card_played: Card
    ):
        """Notifica a todos que un jugador ha jugado una carta."""
        details_model = details.CardPlayedDetails(
            player_id=player_id, card_played=card_played
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_card_discarded(
        self, game_id: int, player_id: int, card_discarded: Card
    ):
        """Notifica a todos que un jugador ha descartado una carta."""
        details_model = details.CardDiscardedDetails(
            player_id=player_id, card=card_discarded
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_player_drew(
        self, game_id: int, player_id: int, deck_size: int
    ):
        """Notifica a todos (públicamente) que un jugador robó del mazo."""
        details_model = details.PlayerDrewFromDeckDetails(
            player_id=player_id, deck_size=deck_size
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_deck_updated(self, game_id: int, deck_size: int):
        """Notifica a todos (públicamente) que el mazo ha sido actualizado."""
        details_model = details.DeckUpdatedDetails(deck_size=deck_size)
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_draft_updated(
        self, game_id: int, card_taken_id: int, new_card: Optional[Card]
    ):
        """
        Notifica a todos en la partida que un slot del draft ha cambiado.
        """
        details_model = details.DraftUpdatedDetails(
            card_taken_id=card_taken_id, new_card=new_card
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_cards_played(
        self, game_id: int, player_id: int,
        cards_played: List[Card], is_cancellable: bool,
        player_name: Optional[str] = None,
        action_id: Optional[int] = None
    ):
        """Notifica a TODOS que un jugador ha jugado un conjunto de cartas (un set)."""
        details_model = details.CardsPlayedDetails(
            player_id=player_id,
            cards_played=cards_played,
            is_cancellable=is_cancellable,
            player_name=player_name,
            action_id=action_id
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(message=message, game_id=game_id)

    async def notify_secret_revealed(
        self,
        game_id: int,
        secret_id: int,
        player_role: PlayerRole,
        player_id: int,
    ):
        """
        Notifica a todos los de la mesa que un secreto ha sido revelado
        Usa el broadcast por partida
        """
        details_model = details.SecretRevealedDetails(
            game_id=game_id,
            secret_id=secret_id,
            role=player_role,
            player_id=player_id,
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_secret_hidden(
        self, game_id: int, secret_id: int, player_id: int
    ):
        details_model = details.SecretHiddenDetails(
            secret_id=secret_id, game_id=game_id, player_id=player_id
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_social_disgrace_applied(
        self, game_id: int, player_id: int
    ):
        details_model = details.SocialDisgraceAppliedDetails(
            player_id=player_id, game_id=game_id
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_social_disgrace_removed(
        self, game_id: int, player_id: int
    ):
        details_model = details.SocialDisgraceRemovedDetails(
            player_id=player_id, game_id=game_id
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_game_over(self, game_id: int):
        details_model = details.GameOverDetails(game_id=game_id)
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_secret_stolen(
        self, game_id: int, thief_id: int, victim_id: int
    ):
        """Notifica a TODOS sobre el robo de un secreto."""
        details_model = details.SecretStolenDetails(
            thief_id=thief_id, victim_id=victim_id
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(message=message, game_id=game_id)

    async def notify_set_created(
        self, game_id: int, player_id: int,
        set_cards: List[Card], is_cancellable: bool
    ):
        """
        Notifica a todos en la partida que se ha creado un nuevo set.
        """
        details_model = details.CardsPlayedDetails(
            player_id=player_id,
            cards_played=set_cards,
            is_cancellable=is_cancellable
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(message=message, game_id=game_id)

    async def notify_set_stolen(
        self,
        game_id: int,
        thief_id: int,
        victim_id: int,
        set_id: int,
        set_cards: List[Card],
    ):
        """Notifica a TODOS sobre el robo de un set."""
        details_model = details.SetStolenDetails(
            thief_id=thief_id,
            victim_id=victim_id,
            set_id=set_id,
            set_cards=set_cards,
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(message=message, game_id=game_id)

    # --- Métodos que notifican a Lobby y Partida (AMBOS) ---

    async def notify_player_joined(
        self,
        game_id: int,
        player_id: int,
        player_name: str,
        updated_game_in_lobby: GameLobbyInfo,
    ):
        """Notifica que un jugador se unió, actualizando la partida y el lobby."""
        # 1. Notificar a los jugadores DENTRO de la partida
        game_details = details.PlayerJoinedDetails(
            player_id=player_id, player_name=player_name, game_id=game_id
        )
        game_message = WSMessage(details=game_details)
        await self.manager.broadcast_to_game(
            game_id=game_id, message=game_message
        )

        # 2. Notificar al LOBBY actualizando el estado de la partida
        lobby_details = details.GameUpdatedDetails(game=updated_game_in_lobby)
        lobby_message = WSMessage(details=lobby_details)
        await self.manager.broadcast_to_lobby(lobby_message)

    async def notify_player_left(
        self,
        game_id: int,
        player_id: int,
        player_name: str,
        updated_game_in_lobby: GameLobbyInfo,
    ):
        """Notifica que un jugador se fue, actualizando la partida y el lobby."""
        # 1. Notificar a los jugadores DENTRO de la partida
        game_details = details.PlayerLeftDetails(
            player_id=player_id,
            player_name=player_name,
            game_id=game_id,
            is_host=(player_id == updated_game_in_lobby.host_id),
        )
        game_message = WSMessage(details=game_details)
        await self.manager.broadcast_to_game(
            game_id=game_id, message=game_message
        )

        # 2. Notificar al LOBBY actualizando el estado de la partida
        lobby_details = details.GameUpdatedDetails(game=updated_game_in_lobby)
        lobby_message = WSMessage(details=lobby_details)
        await self.manager.broadcast_to_lobby(lobby_message)

    async def notify_game_started(
        self,
        game_id: int,
        first_player_id: int,
        players_in_turn_order: List[int],
        updated_game_in_lobby: GameLobbyInfo,
    ):
        """Notifica que la partida empezó, actualizando la partida y el lobby."""
        # 1. Notificar a los jugadores DENTRO de la partida con todos los detalles
        game_details = details.GameStartedDetails(
            game_id=game_id,
            first_player_id=first_player_id,
            players_in_turn_order=players_in_turn_order,
        )
        game_message = WSMessage(details=game_details)
        await self.manager.broadcast_to_game(
            game_id=game_id, message=game_message
        )

        # 2. Notificar al LOBBY actualizando el estado de la partida a "iniciada"
        lobby_details = details.GameUpdatedDetails(game=updated_game_in_lobby)
        lobby_message = WSMessage(details=lobby_details)
        await self.manager.broadcast_to_lobby(lobby_message)

    # --- Métodos que notifican a UN Jugador especifico dentro de una Partida especifica ---

    async def notify_player_to_reveal_secret(
        self, game_id: int, player_id: int
    ):
        """
        Notifica a un jugador ESPECÍFICO que debe elegir un secreto para revelar.
        Usa el broadcast privado.
        """
        details_model = details.PlayerToRevealSecretDetails()
        message = WSMessage(details=details_model)
        await self.manager.send_to_player(
            message=message, game_id=game_id, player_id=player_id
        )

    async def notify_player_to_choose_card(
        self, game_id: int, player_id: int, cards: List[Card]
    ):
        """Notifica a un jugador ESPECIFICO que debe elegir una carta para robar."""

        details_model = details.PromptDrawFromDiscardDetails(cards=cards)
        message = WSMessage(details=details_model)
        await self.manager.send_to_player(
            message=message, game_id=game_id, player_id=player_id
        )

    async def notify_player_to_choose_card_for_trade(
        self, game_id: int, player_id: int, initiator_player_id: int
    ):
        """Notifica a un jugador ESPECÍFICO que debe elegir una carta para intercambiar."""
        details_model = details.TradeRequestedDetails(
            initiator_player_id=initiator_player_id
        )
        message = WSMessage(details=details_model)
        await self.manager.send_to_player(
            message=message, game_id=game_id, player_id=player_id
        )

    async def notify_hand_updated(
        self, game_id: int, player_id: int, hand: List[Card]
    ):
        """Notifica a un jugador ESPECÍFICO que su mano ha sido actualizada."""
        from ...websockets.protocol.details import HandUpdatedDetails

        details_model = HandUpdatedDetails(hand=hand)
        message = WSMessage(details=details_model)
        await self.manager.send_to_player(
            message=message, game_id=game_id, player_id=player_id
        )

    async def notify_cards_NSF_discarded(
        self,
        game_id: int,
        source_player_id: int,
        target_player_id: int,
        discarded_cards: List[Card],
    ):
        """
        Notifica a TODOS que un jugador ha obligado a otro a descartar
        todas sus cartas de tipo 'Not So Fast'.
        """
        details_model = details.CardsNSFDiscardedDetails(
            source_player_id=source_player_id,
            target_player_id=target_player_id,
            discarded_cards=discarded_cards,
        )
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(game_id=game_id, message=message)

    async def notify_request_to_donate_card_dcf(
        self,
        game_id: int,
        direction: Literal["left", "right"],
    ):
        """
        Notifica que "tienes que donar una carta al jugador de {direction = [ left right ]}
        """
        details_model = details.RequestToDonateDetails(direction=direction)
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(message=message, game_id=game_id)

    async def notify_players_to_vote(self, game_id: int):
        """Notifica a todos los jugadores que se ha iniciado una votación."""
        details_model = details.VoteStartedDetails()
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(message=message, game_id=game_id)

    # ¡¡¡Y LA SEGUNDA FUNCIÓN, TAMBIÉN CORREGIDA!!!
    async def notify_vote_result(
        self, game_id: int, most_voted_id: Optional[int], was_tie: bool
    ):
        """Notifica el resultado de la votación a todos los jugadores."""

        # 1. Creamos el MODELO de detalles.
        details_model = details.VoteEndedDetails(
            most_voted_player_id=most_voted_id,
            tie=was_tie,
        )

        # 2. Lo envolvemos y lo enviamos.
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(message=message, game_id=game_id)

    async def notify_hands_updated(self, game_id: int):
        details_model = details.HandsUpdatedDetails()
        message = WSMessage(details=details_model)
        await self.manager.broadcast_to_game(message=message, game_id=game_id)
        
    async def notify_action_cancelled(
        self, game_id: int, player_id: int, cards: List[Card]
    ):
        """Notifica a TODOS que la acción de un jugador ha sido cancelada."""
        print(f"[NOTIFICATOR] notify_action_cancelled: game_id={game_id}, player_id={player_id}, cards_count={len(cards)}")
        details_model = details.PlayerActionCancelledDetails(
            player_id=player_id, cards_cancelled=cards
        )
        message = WSMessage(details=details_model)
        print(f"[NOTIFICATOR] Mensaje ACTION_CANCELLED construido, broadcasting...")
        await self.manager.broadcast_to_game(game_id=game_id, message=message)
        print(f"[NOTIFICATOR] ACTION_CANCELLED enviado")

    async def notify_action_resolved(
        self, game_id: int, player_id: int, cards: List[Card],
        action_id: Optional[int] = None
    ):
        """Notifica a TODOS que la acción de un jugador ha sido resuelta."""
        print(f"[NOTIFICATOR] notify_action_resolved: game_id={game_id}, player_id={player_id}, cards_count={len(cards)}, action_id={action_id}")
        details_model = details.PlayerActionResolvedDetails(
            player_id=player_id, cards_resolved=cards, action_id=action_id
        )
        message = WSMessage(details=details_model)
        print(f"[NOTIFICATOR] Mensaje ACTION_RESOLVED construido, broadcasting...")
        await self.manager.broadcast_to_game(game_id=game_id, message=message)
        print(f"[NOTIFICATOR] ACTION_RESOLVED enviado")
