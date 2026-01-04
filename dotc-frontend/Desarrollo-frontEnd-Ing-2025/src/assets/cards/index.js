import cardBack from './01-card_back.png';
import murdererEscapes from './02-murder_escapes.png';
import secretMurderer from './03-secret_murderer.png';
import secretAccomplice from './04-secret_accomplice.png';
import secretBack from './05-secret_back.png';
import secretFront from './06-secret_front.png';
import herculePoirot from './07-detective_poirot.png';
import missMarple from './08-detective_marple.png';
import mrSatterthwaite from './09-detective_satterthwaite.png';
import parkerPyne from './10-detective_pyne.png';
import ladyEileen from './11-detective_brent.png'; // Asumo que Brent es Lady Eileen
import tommyBeresford from './12-detective_tommyberesford.png';
import tuppenceBeresford from './13-detective_tuppenceberesford.png';
import harleyQuin from './14-detective_quin.png';
import ariadneOliver from './15-detective_oliver.png';
import notSoFast from './16-Instant_notsofast.png';
import cardsOffTheTable from './17-event_cardsonthetable.png';
import anotherVictim from './18-event_anothervictim.png';
import deadCardFolly from './19-event_deadcardfolly.png';
import lookIntoTheAshes from './20-event_lookashes.png';
import cardTrade from './21-event_cardtrade.png';
import thereWasOneMore from './22-event_onemore.png';
import delayMurdererEscape from './23-event_delayescape.png';
import earlyTrain from './24-event_earlytrain.png';
import pointYourSuspicions from './25-event_pointsuspicions.png';
import blackmailed from './26-devious_blackmailed.png';
import socialFauxPas from './27-devious_fauxpas.png';

// Objeto que mapea el `type` de la carta a su imagen importada
const cardTypeToImage = {
    // Secrets
    "MURDERER": secretMurderer,
    "ACCOMPLICE": secretAccomplice,
    "INNOCENT": secretFront, 
    "SECRET_BACK": secretBack,

    // Detectives
    "Harley Quin": harleyQuin,
    "Ariadne Oliver": ariadneOliver,
    "Miss Marple": missMarple,
    "Parker Pyne": parkerPyne,
    "Tommy Beresford": tommyBeresford,
    "Lady Eileen": ladyEileen,
    "Tuppence Beresford": tuppenceBeresford,
    "Hercule Poirot": herculePoirot,
    "Mr Satterthwaite": mrSatterthwaite,

    // Instant
    "Not So Fast": notSoFast,

    // Devious
    "Blackmailed": blackmailed,
    "Social Faux Pas": socialFauxPas,

    // Event
    "Delay the murderer's escape!": delayMurdererEscape,
    "Point your suspicions": pointYourSuspicions,
    "Dead card folly": deadCardFolly,
    "Another Victim": anotherVictim,
    "Look into the ashes": lookIntoTheAshes,
    "Card trade": cardTrade,
    "And then there was one more...": thereWasOneMore,
    "Early train to Paddington": earlyTrain,
    "Cards off the table": cardsOffTheTable,

    // End of game
    "Murderer Escapes!": murdererEscapes,
    
    // Casos especiales como el reverso de la carta
    "CARD_BACK": cardBack
};

// Nueva función helper que busca por `cardType`
export const getCardImage = (cardType) => {
    const image = cardTypeToImage[cardType];
    
    if (!image) {
        console.warn(`No se encontró imagen para el tipo de carta: ${cardType}. Usando reverso.`);
        return cardBack; // Devuelve una imagen por defecto si no encuentra el tipo
    }

    return image;
};