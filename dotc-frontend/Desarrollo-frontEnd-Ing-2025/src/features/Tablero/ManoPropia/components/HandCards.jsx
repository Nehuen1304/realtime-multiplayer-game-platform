import { Carta } from '../../../../components/Carta/Carta';
import { useTouchHover } from '../hooks/useTouchHover';

export function HandCards({ mano, puedoJugar, seJugo, selectedCardsIds, onSelectCard, nsfWindowOpen }) {
  // Permitir clicks cuando:
  // 1. Hay ventana NSF abierta (nsfWindowOpen) -> siempre permitir clicks para cancelar
  // 2. Es tu turno Y no has jugado todavía (!seJugo && puedoJugar)
  // 
  // Mejora: Si hay NSF abierta, permitir clicks incluso si ya jugaste
  const isDisabled = nsfWindowOpen ? false : (seJugo || !puedoJugar);

  const { containerRef, hoveredIndex, setHoveredIndex, bind } = useTouchHover({
    isDisabled,
    longPressMs: 250,
    onSelectIndex: (idx) => {
      const card = mano[idx];
      console.log('🎴 useTouchHover onSelectIndex:', { idx, card, isDisabled });
      if (card) onSelectCard(card);
    },
  });
  const showWaitingOverlay = !puedoJugar && !nsfWindowOpen;

  return (
    <div
      ref={containerRef}
      className={`cartas-wrapper ${isDisabled ? 'disabled' : ''}`}
      data-hovered={hoveredIndex !== null ? 'true' : 'false'}
      data-nsf-active={nsfWindowOpen ? 'true' : 'false'}
      style={{ '--hover': hoveredIndex ?? 0, '--step': '4rem', '--overlap': '5rem' }}
      {...(nsfWindowOpen ? {} : bind)}
    >
      {
      showWaitingOverlay && <div className="waiting-turn">Esperando tu turno...</div>
      }
      {seJugo && mano.length < 6 && (
        <div className="waiting-turn">Debes robar cartas hasta tener 6 para poder pasar el turno.</div>
      )}

      {mano.map((carta, i) => {
        const diff = hoveredIndex === null ? undefined : i - hoveredIndex;
        const isSelected = selectedCardsIds.includes(carta.card_id);
        
        const handleClick = () => {
          console.log('🖱️ Click en carta:', { 
            card_id: carta.card_id, 
            card_type: carta.card_type, 
            isDisabled, 
            nsfWindowOpen 
          });
          if (!isDisabled) {
            onSelectCard(carta);
          }
        };
        
        return (
          <Carta
            key={carta.card_id}
            cartaData={carta}
            isSelected={isSelected}
            onCardClick={handleClick}
            onMouseEnter={() => !isDisabled && setHoveredIndex(i)}
            onMouseLeave={() => setHoveredIndex(null)}
            style={{ '--i': i, cursor: isDisabled ? 'default' : 'pointer' }}
            dataDiff={diff}
          />
        );
      })}
    </div>
  );
}
