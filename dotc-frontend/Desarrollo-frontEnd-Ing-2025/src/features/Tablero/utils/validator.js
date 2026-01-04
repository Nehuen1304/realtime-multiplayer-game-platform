const detectives = new Set( [
        // Detectives
        "Harley Quin",
        "Ariadne Oliver",
        "Miss Marple",
        "Parker Pyne",
        "Tommy Beresford",
        "Lady Eileen",
        "Tuppence Beresford",
        "Hercule Poirot",
        "Mr Satterthwaite"
]);
const eventos = new Set( [
        // Eventos
        "Delay the murderer's escape!",
        "Point your suspicions",
        "Dead card folly",
        "Another Victim",
        "Look into the ashes",
        "Card trade",
        "And then there was one more...",
        "Early train to Paddington",
        "Cards off the table"
]);
// Nombre canónico de la carta NSF
const NOT_SO_FAST_NAME = "Not So Fast";
/*
  selectedCardIds,
  selectTypesCardIds,
  targetPlayerId: playSel?.targetPlayerId ?? null,
  targetSecretId: playSel?.targetSecretId ?? null,
  targetCardId: playSel?.targetCardId ?? null,
  targetSetId: playSel?.targetSetId ?? null,
  actionType: playSel?.actionType ?? null
*/


/*
 selectedCardIds,
    selectTypesCardIds,
    targetPlayerId: playSel?.targetPlayerId ?? null,
    targetSecretId: playSel?.targetSecretId ?? null,
    targetCardId: playSel?.targetCardId ?? null,
    targetSetId: playSel?.targetSetId ?? null,
    actionType: playSel?.actionType ?? null

*/
export function canFormDetectiveSet(selectionState) {
    
if(selectionState.selectedCardIds.length<2){
    return false;
}

const type_of_cards_played= []
 for(const t of selectionState.selectTypesCardIds){
    if(!detectives.has(t[0])){
        return false;
    }
    if(t[0]!=="Harley Quin"){
        if(!(type_of_cards_played.includes(t[0]))){
        type_of_cards_played.push(t[0]);
    }
 }
}

    if(type_of_cards_played.includes("Ariadne Oliver")){
        return false;
    }


 if(type_of_cards_played.length===0 || type_of_cards_played.length>2){
    return false;
 }

const harley_count = (selectionState.selectTypesCardIds || []).filter(t => t[0] === "Harley Quin").length;
 if(type_of_cards_played.length === 1){
    if(type_of_cards_played[0]==="Hercule Poirot" || type_of_cards_played[0]==="Miss Marple"){
        if(selectionState.selectedCardIds.length!==3){
            return false;
    }
        if (harley_count > 2) {
            return false;
        }
        if(selectionState.targetSecretId===null){
            return false;
        }
        if(selectionState.targetPlayerId===null){
            return false; 
        }
    }
    const set_detective_of_two_value = ["Parker Pyne","Tommy Beresford","Lady Eileen","Tuppence Beresford","Mr Satterthwaite"];
    if(set_detective_of_two_value.includes(type_of_cards_played[0])){
        if(selectionState.selectedCardIds.length!==2){
            return false;
        }
        if (harley_count > 1) {
            return false;
        }
        if(selectionState.targetPlayerId===null){
            return false; 
        }
    }
 }

 if(type_of_cards_played.length === 2){
    const brothers_cards = ["Tommy Beresford","Tuppence Beresford"];
    if(!(brothers_cards.includes(type_of_cards_played[0]) && brothers_cards.includes(type_of_cards_played[1]))){
        return false;
    }
        if (harley_count > 2) {
            return false;
        }   
    if(selectionState.selectedCardIds.length>4){
        return false;
    }
    if(selectionState.targetPlayerId===null){
            return false; 
        }
 }
return true;

}


export function canShareTextFromDetectiveSet(selectionState)  {
    const harley_count = (selectionState.selectTypesCardIds || []).filter(t => t[0] === "Harley Quin").length;
    const type_of_cards_played= []
 for(const t of selectionState.selectTypesCardIds){
    if(!detectives.has(t[0])){
        return false;
    }
    if(t[0]!=="Harley Quin"){
        if(!(type_of_cards_played.includes(t[0]))){
        type_of_cards_played.push(t[0]);
        }
 }
}
    if(type_of_cards_played.length>2){
        return false;
    }
    if(type_of_cards_played.length === 0 && harley_count===0){
        return false;
    }
    if(type_of_cards_played.length === 1){
        //Una excepción dado el funcionamiento de textoSugerencia
        if(type_of_cards_played[0]==="Ariadne Oliver"&& harley_count===0){
            console.log("entra");
            return true;
        }
        if(type_of_cards_played[0]==="Hercule Poirot" || type_of_cards_played[0]==="Miss Marple"){
        if(selectionState.selectedCardIds.length!==3){
            return false;
    }
        if (harley_count > 2) {
            return false;
        }
    }
    const set_detective_of_two_value = ["Parker Pyne","Tommy Beresford","Lady Eileen","Tuppence Beresford","Mr Satterthwaite"];
    if(set_detective_of_two_value.includes(type_of_cards_played[0])){
        if(selectionState.selectedCardIds.length!==2){
            return false;
        }
        if (harley_count > 1) {
            return false;
        }
    }
 }

 if(type_of_cards_played.length === 2){
    const brothers_cards = ["Tommy Beresford","Tuppence Beresford"];
    if(!(brothers_cards.includes(type_of_cards_played[0]) && brothers_cards.includes(type_of_cards_played[1]))){
        return false;
    }
        if (harley_count > 2) {
            return false;
        }   
    if(selectionState.selectedCardIds.length>4){
        return false;
    }
 }
 return true;

}


export function canPlayEvent(selectionState) {
 if (!selectionState || !Array.isArray(selectionState.selectedCardIds) || selectionState.selectedCardIds.length !== 1) {
        return false;
    }

    const eventType = selectionState.selectTypesCardIds?.[0]?.[0];
    if (!eventType || !eventos.has(eventType)) {
        return false;
    }

    // Validaciones específicas por evento (usar los nombres exactamente como en `eventos`)
    switch (eventType) {
        case "Card trade":
        case "Cards off the table":
            // Requieren seleccionar un jugador objetivo
            return selectionState.targetPlayerId != null;

        case "Another Victim":
            // Requiere seleccionar un set en la mesa
            return selectionState.targetSetId != null;

        case "And then there was one more...":
            // Requiere seleccionar una carta secreta y un jugador (dónde añadirla)
            return selectionState.targetSecretId != null && selectionState.targetPlayerId != null;

        case "Dead card folly":
            // Requiere decidir una dirección antes de jugar: usar actionType 'left' o 'right'
            // return typeof selectionState.actionType === "string" && ["left", "right"].includes(selectionState.actionType);
            return true;
        case "Card trade":
            return selectionState.targetCardId != null && selectionState.targetPlayerId != null;
        case "Look into the ashes":
        case "Delay the murderer's escape!":
        case "Point your suspicions":
        case "Early train to Paddington":
            // No requieren objetivos pre-seleccionados; la interacción se resuelve después de jugar
            return true;

        default:
            return false;
    }
}


export function canShowEventText(selectionState) {
    if (selectionState.selectedCardIds.length !== 1) {
        return false;
    }
    if (!selectionState.selectTypesCardIds || selectionState.selectTypesCardIds.length === 0) {
        return false;
    }
    return eventos.has(selectionState.selectTypesCardIds[0][0]);
}




export function canAddToDetectiveSet(selectionState) {
    // 1. Debe haber exactamente 1 carta seleccionada
    if (selectionState.selectedCardIds.length !== 1) {
        return false;
    }

    // 2. La carta debe ser un detective
    const cardType = selectionState.selectTypesCardIds?.[0]?.[0];
    if (!cardType || !detectives.has(cardType)) {
        return false;
    }

    // 3. Debe haber un set objetivo seleccionado
    if (selectionState.targetSetId == null) {
        return false;
    }

    // 4. Necesitamos saber el tipo del set objetivo
    const setType = selectionState.targetSetType;
    if (!setType) {
        // Aún no se ha cargado el tipo de set
        return false;
    }

    // 5. No se puede añadir *a* un set de "Ariadne Oliver" (ella es un set de 1)
    if (setType === "Ariadne Oliver") {
        return false;
    }

    // 6. REGLA: "Ariadne Oliver" (Caso especial)
    if (cardType === "Ariadne Oliver") {
        // SOLO se puede añadir a un set de OPONENTE
        // NO se puede añadir a tu propio set
        return !selectionState.isTargetSetOwnedByMe;
    }

    // 7. REGLA: Todas las demás cartas (Caso General)
    // SOLO se pueden añadir a sets PROPIOS
    if (!selectionState.isTargetSetOwnedByMe) {
        // No es Ariadne, y el set no es mío -> Inválido
        return false;
    }

    // --- Llegados a este punto, es un set PROPIO y una carta que NO es Ariadne ---

    // 8. Validación de tipo (en set propio)

    // 8a. Harley Quin (comodín) siempre se puede añadir (a un set propio)
    if (cardType === "Harley Quin") {
        return true;
    }

    // 8b. Caso especial: Set de "Tommy y Tuppence Beresford"
    if (setType === "Tommy y Tuppence Beresford") {
        return cardType === "Tommy Beresford" || cardType === "Tuppence Beresford";
    }

    // 8c. Caso normal: El tipo de la carta debe coincidir con el tipo del set
    return cardType === setType;
}

// Habilita el botón "Not So Fast" sólo cuando:
// - Hay exactamente 1 carta seleccionada
// - Esa carta es "Not So Fast..."
// - La ventana NSF está abierta y el jugador no respondió aún
// - Opcional: el jugador actual es distinto de quien jugó la acción cancelable
export function canPlayNSF(selectionState, { nsfWindowOpen = false, alreadyResponded = false, currentPlayerId = null, windowPlayedBy = null } = {}) {
    if (!nsfWindowOpen || alreadyResponded) return false;
    if (!selectionState || !Array.isArray(selectionState.selectedCardIds) || selectionState.selectedCardIds.length !== 1) return false;
    
    // Mirar el ÚLTIMO tipo de carta seleccionada, no el primero
    // Esto permite tener selecciones previas y aun así poder jugar NSF
    const types = selectionState.selectTypesCardIds;
    const lastType = types && types.length > 0 ? types[types.length - 1]?.[0] : null;
    
    if (currentPlayerId != null && windowPlayedBy != null && String(currentPlayerId) === String(windowPlayedBy)) return false;
    return lastType === NOT_SO_FAST_NAME;
}

