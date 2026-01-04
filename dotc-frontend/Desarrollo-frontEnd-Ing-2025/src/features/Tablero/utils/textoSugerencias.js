// Helper para obtener el detective principal del set
export const getDetectivePrincipal = (selectTypesCardIds) => {
    if (!Array.isArray(selectTypesCardIds)) return null;
    // Filtra detectives, ignora Harley Quin
    const detectives = selectTypesCardIds
        .map(([type]) => type)
        .filter(type => type !== "Harley Quin");
    const types = selectTypesCardIds.map(([type]) => type);
    const uniqueTypes = new Set(types);
    // Eliminar duplicados usando Set
    const uniqueDetectives = [...new Set(detectives)];
    console.log("Como es selectTypesCardIds", selectTypesCardIds);
    if (uniqueDetectives.length === 0 && selectTypesCardIds[0][0] === "Harley Quin") {
        return "Harley Quin";
    }
    if (uniqueTypes.has("Mr Satterthwaite") && uniqueTypes.has("Harley Quin")) {
        
        // Contamos cuántos tipos de detectives *diferentes* hay (sin contar Harley)
        const otherDetectiveTypes = [...uniqueTypes].filter(
            t => t !== "Harley Quin" && t !== "Mr Satterthwaite"
        );
        
        // Si NO hay otros tipos de detectives, es nuestro combo
        if (otherDetectiveTypes.length === 0) {
             return "Mr Satterthwaite y Harley Quin"; // Devolvemos un NUEVO string combinado
        }
        // Si hay otros (ej: Satterthwaite, Harley, Marple), Harley actúa como comodín normal
    }
    if (uniqueDetectives.length === 2) {
        if(uniqueDetectives.includes("Tommy Beresford") && uniqueDetectives.includes("Tuppence Beresford")) {
            return "Tommy y Tuppence Beresford";
        }
    }
    
    return uniqueDetectives[0] || "Detective";
};
export const getEvetoText = (evento) => {
    switch (evento) {
        case "And then there was one more...":
            return "Elige un secreto revelado (de cualquier jugador) y luego un jugador para dárselo.";
        
        case "Dead card folly":
            return "Juega para forzar a todos a pasar una carta (izquierda o derecha).";

        case "Look into the ashes":
            return "Juega para ver las 5 primeras cartas del descarte y elegir una para tu mano.";

        case "Card trade":
            return "Elige un oponente y la carta a intercambiar para intercambiar una carta de tu mano con él.";

        case "Delay the murderer's escape!":
            return "Juega para mover hasta 5 cartas del descarte al mazo.";

        case "Early train to Paddington":
            return "Juega para descartar las 6 primeras cartas del mazo.";

        case "Point your suspicions":
            return "Juega para iniciar una votación. ¡El jugador más votado deberá revelar un secreto!";

        case "Another Victim":
            return "¡Elige un set de detective de un oponente para robarlo!";

        default:
            return "Juega este evento para activar su efecto.";
    }
}
export const getDetectiveText = (detective) => {
    switch (detective) {
        case "Hercule Poirot":
            return "¡Puedes elegir el secreto de un oponente para revelar!";
        case "Miss Marple":
            return "¡Puedes elegir el secreto de un oponente para revelar!";
        case "Lady Eileen":
            return "¡Elige un oponente para que revele un secreto (de elección de él)...";
        case "Tommy Beresford":
            return "¡Elige un oponente para que revele un secreto (de elección de él)...";
        case "Tuppence Beresford":
            return "¡Elige un oponente para que revele un secreto (de elección de él)...";
        case "Mr Satterthwaite":
            return "¡Elige un oponente para que revele un secreto!";
        case "Parker Pyne":
            return " ¡Puedes ocultar una carta de secreto ya revelada!";
        case "Ariadne Oliver":
            return "¡Agrega este set al de un oponente para que revele un secreto!";
        case "Harley Quin":
            return "Harley Quin es comodín: úsalo para completar cualquier set de detective.";
        case "Tommy y Tuppence Beresford":
            return "¡Elige un oponente para que revele un secreto (de elección de él)... No podrá ser cancelado!!!";
        case "Mr Satterthwaite y Harley Quin":
            return "Elige un jugador para robarle un Secreto"
        default:
            return "Selecciona detectives para formar un set válido.";
    }
};


export const getEventoText = (evento) => {
    switch (evento) {
        case "Card trade":
            return "Elige a un oponente y una carta que este tenga. Ambos intercambiarán en secreto una carta de su mano.";
        case "Another Victim":
            return "Elige un set de detective que un oponente tenga en la mesa y róbalo para ti.";
        case "Look into the ashes":
            return "Revisa las 5 cartas superiores de la pila de descarte y elige una para añadirla a tu mano.";
        case "Dead card folly":
            return "Decide una dirección (izquierda o derecha). Todos los jugadores pasarán una carta de su mano en esa dirección.";
        case "Delay the murderer's escape!":
            return "Envia hasta 5 cartas del mazo de descarte al mazo de robo.";
        case "Cards off the table":
            return "Elige a un jugador. Ese jugador se ve obligado a descartar todas las cartas Not So Fast... que tenga en su mano.";
        case "And then there was one more...":
            return "Elige una carta secreta que ya esté revelada en la mesa y añádela (boca abajo) a los secretos de cualquier jugador, incluyéndote a ti.";
        case "Point your suspicions":
            return "Inicia una votación. Todos señalarán a la vez a quien crean que es el Asesino. El jugador con más votos deberá revelar un secreto.";
        case "Early train to Paddington":
            return "Descarta las 6 cartas superiores del mazo de robo. Esto acelera el final del juego!!!";
        default:
            return "Esta es una carta de evento.";
    }
};