from pydantic import BaseModel, Field
from typing import Union

from . import details  # Importo todo de details

# Crea la Union con TODOS los modelos de detalles que existen.
AnyDetails = Union[
    # Modelos del Lobby
    details.GameCreatedDetails,
    details.GameUpdatedDetails,
    details.GameRemovedDetails,
    # Modelos de Partida (Públicos)
    details.NewTurnDetails,
    details.CardPlayedDetails,
    details.CardDiscardedDetails,
    details.PlayerDrewFromDeckDetails,
    details.SecretRevealedDetails,
    details.DeckUpdatedDetails,
    details.DraftUpdatedDetails,
    details.PlayerToRevealSecretDetails,
    details.CardsPlayedDetails,
    details.SecretStolenDetails,
    details.SecretHiddenDetails,
    details.SetStolenDetails,
    details.PromptDrawFromDiscardDetails,
    details.CardsNSFDiscardedDetails,
    details.HandUpdatedDetails,
    details.PlayerActionCancelledDetails,
    details.PlayerActionResolvedDetails,
    details.SocialDisgraceAppliedDetails,
    details.RequestToDonateDetails,
    details.SocialDisgraceRemovedDetails,
    details.GameOverDetails,
    details.VoteStartedDetails,
    details.VoteEndedDetails,
    details.HandUpdatedDetails,
    details.TradeRequestedDetails,
    # Modelos que afectan a ambos
    details.PlayerJoinedDetails,
    details.PlayerLeftDetails,
    details.GameStartedDetails,
]


class WSMessage(BaseModel):
    # Usamos Field con 'discriminator' para que Pydantic sepa como
    # validar y serializar el modelo correcto dentro de la Union.
    details: AnyDetails = Field(..., discriminator="event")
