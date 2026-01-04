export const CARDS_OFF_THE_TABLE = 'Cards off the table';

export const CARDS_OFF_THE_TABLE_HELP = 'Elige un jugador para que descarte todos sus NSF';

export const isCardsOffTheTable = (cardType) => {
  return cardType === CARDS_OFF_THE_TABLE;
};

export const requiresTargetPlayer = (cardType) => {
  return cardType === CARDS_OFF_THE_TABLE;
};
