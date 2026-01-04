import { describe, it, expect } from 'vitest';
import { canFormDetectiveSet, canPlayEvent, canAddToDetectiveSet } from './validator.js';

describe('validator - canFormDetectiveSet', () => {
  describe('Casos válidos - Detective de 3 cartas', () => {
    it('permite Hercule Poirot con 3 cartas y targets', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2, 3],
        selectTypesCardIds: [['Hercule Poirot', 1], ['Hercule Poirot', 2], ['Hercule Poirot', 3]],
        targetPlayerId: 5,
        targetSecretId: 10,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(true);
    });

    it('permite Miss Marple con 2 cartas + 1 Harley', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2, 3],
        selectTypesCardIds: [['Miss Marple', 1], ['Harley Quin', 2], ['Harley Quin', 3]],
        targetPlayerId: 5,
        targetSecretId: 10,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(true);
    });
  });

  describe('Casos válidos - Detective de 2 cartas', () => {
    it('permite Parker Pyne con 2 cartas', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2],
        selectTypesCardIds: [['Parker Pyne', 1], ['Parker Pyne', 2]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(true);
    });

    it('permite Tommy con 1 carta + 1 Harley', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2],
        selectTypesCardIds: [['Tommy Beresford', 1], ['Harley Quin', 2]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(true);
    });
  });

  describe('Casos válidos - Hermanos Beresford', () => {
    it('permite Tommy + Tuppence con 2 cartas', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2],
        selectTypesCardIds: [['Tommy Beresford', 1], ['Tuppence Beresford', 2]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(true);
    });

    it('permite Tommy + Tuppence con 4 cartas', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2, 3, 4],
        selectTypesCardIds: [['Tommy Beresford', 1], ['Tommy Beresford', 2], ['Tuppence Beresford', 3], ['Tuppence Beresford', 4]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(true);
    });
  });

  describe('Casos inválidos - Cantidad insuficiente', () => {
    it('rechaza 0 o 1 carta', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1],
        selectTypesCardIds: [['Hercule Poirot', 1]],
        targetPlayerId: 5,
        targetSecretId: 10,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });
  });

  describe('Casos inválidos - Ariadne Oliver', () => {
    it('rechaza Ariadne Oliver (no forma sets)', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2],
        selectTypesCardIds: [['Ariadne Oliver', 1], ['Ariadne Oliver', 2]],
        targetPlayerId: 5,
        targetSetId: 99,
        targetSecretId: null,
        targetCardId: null,
        actionType: null,
      })).toBe(false);
    });
  });

  describe('Casos inválidos - Cartas inválidas', () => {
    it('rechaza si hay cartas no-detective', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2],
        selectTypesCardIds: [['Parker Pyne', 1], ['Another Victim', 2]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });

    it('rechaza solo Harley Quin', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2],
        selectTypesCardIds: [['Harley Quin', 1], ['Harley Quin', 2]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });
  });

  describe('Casos inválidos - Cantidad incorrecta por detective', () => {
    it('rechaza Hercule Poirot con 2 cartas', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2],
        selectTypesCardIds: [['Hercule Poirot', 1], ['Hercule Poirot', 2]],
        targetPlayerId: 5,
        targetSecretId: 10,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });

    it('rechaza Parker Pyne con 3 cartas', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2, 3],
        selectTypesCardIds: [['Parker Pyne', 1], ['Parker Pyne', 2], ['Parker Pyne', 3]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });

    it('rechaza hermanos Beresford con 5 cartas', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2, 3, 4, 5],
        selectTypesCardIds: [['Tommy Beresford', 1], ['Tommy Beresford', 2], ['Tuppence Beresford', 3], ['Tuppence Beresford', 4], ['Harley Quin', 5]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });
  });

  describe('Casos inválidos - Targets faltantes', () => {
    it('rechaza Hercule sin targetSecretId', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2, 3],
        selectTypesCardIds: [['Hercule Poirot', 1], ['Hercule Poirot', 2], ['Hercule Poirot', 3]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });

    it('rechaza detective sin targetPlayerId', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2],
        selectTypesCardIds: [['Parker Pyne', 1], ['Parker Pyne', 2]],
        targetPlayerId: null,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });
  });

  describe('Casos inválidos - Harley Quin exceso', () => {
    it('rechaza 3 Harley para Hercule', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2, 3],
        selectTypesCardIds: [['Harley Quin', 1], ['Harley Quin', 2], ['Harley Quin', 3]],
        targetPlayerId: 5,
        targetSecretId: 10,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });

    it('rechaza 2 Harley para detective de 2 cartas', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2],
        selectTypesCardIds: [['Harley Quin', 1], ['Harley Quin', 2]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });
  });

  describe('Casos inválidos - Combinaciones incorrectas', () => {
    it('rechaza Tommy + Parker Pyne (no hermanos)', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2, 3, 4],
        selectTypesCardIds: [['Tommy Beresford', 1], ['Tommy Beresford', 2], ['Parker Pyne', 3], ['Parker Pyne', 4]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });

    it('rechaza 3 tipos diferentes', () => {
      expect(canFormDetectiveSet({
        selectedCardIds: [1, 2, 3],
        selectTypesCardIds: [['Parker Pyne', 1], ['Tommy Beresford', 2], ['Lady Eileen', 3]],
        targetPlayerId: 5,
        targetSecretId: null,
        targetCardId: null,
        targetSetId: null,
        actionType: null,
      })).toBe(false);
    });
  });
});

describe('validator - canPlayEvent', () => {
  it('permite jugar evento válido', () => {
    expect(canPlayEvent({
      selectedCardIds: [1],
      // Usamos un evento que no requiere objetivos preseleccionados
      selectTypesCardIds: [['Early train to Paddington', 1]],
      targetPlayerId: null,
      targetSecretId: null,
      targetCardId: null,
      targetSetId: null,
      actionType: null,
    })).toBe(true);
  });

  it('rechaza si hay múltiples cartas', () => {
    expect(canPlayEvent({
      selectedCardIds: [1, 2],
      selectTypesCardIds: [['Another Victim', 1], ['Card trade', 2]],
      targetPlayerId: null,
      targetSecretId: null,
      targetCardId: null,
      targetSetId: null,
      actionType: null,
    })).toBe(false);
  });

  it('rechaza si no es evento (es detective)', () => {
    expect(canPlayEvent({
      selectedCardIds: [1],
      selectTypesCardIds: [['Hercule Poirot', 1]],
      targetPlayerId: null,
      targetSecretId: null,
      targetCardId: null,
      targetSetId: null,
      actionType: null,
    })).toBe(false);
  });

  it('rechaza si tipo no existe', () => {
    expect(canPlayEvent({
      selectedCardIds: [1],
      selectTypesCardIds: [['Carta Inventada', 1]],
      targetPlayerId: null,
      targetSecretId: null,
      targetCardId: null,
      targetSetId: null,
      actionType: null,
    })).toBe(false);
  });
});

describe('validator - canAddToDetectiveSet', () => {
  it('permite añadir Ariadne Oliver con targetSetId', () => {
    expect(canAddToDetectiveSet({
      selectedCardIds: [1],
      selectTypesCardIds: [['Ariadne Oliver', 1]],
      targetPlayerId: null,
      targetSecretId: null,
      targetCardId: null,
      targetSetId: 55,
      targetSetType: 'Hercule Poirot',
      isTargetSetOwnedByMe: false,
      actionType: null,
    })).toBe(true);
  });

  it('permite añadir detective válido con targetSetId', () => {
    expect(canAddToDetectiveSet({
      selectedCardIds: [1],
      selectTypesCardIds: [['Parker Pyne', 1]],
      targetPlayerId: null,
      targetSecretId: null,
      targetCardId: null,
      targetSetId: 55,
      targetSetType: 'Parker Pyne',
      isTargetSetOwnedByMe: true,
      actionType: null,
    })).toBe(true);
  });

  it('rechaza si hay múltiples cartas', () => {
    expect(canAddToDetectiveSet({
      selectedCardIds: [1, 2],
      selectTypesCardIds: [['Ariadne Oliver', 1], ['Ariadne Oliver', 2]],
      targetPlayerId: null,
      targetSecretId: null,
      targetCardId: null,
      targetSetId: 55,
      actionType: null,
    })).toBe(false);
  });

  it('rechaza Harley Quin', () => {
    expect(canAddToDetectiveSet({
      selectedCardIds: [1],
      selectTypesCardIds: [['Harley Quin', 1]],
      targetPlayerId: null,
      targetSecretId: null,
      targetCardId: null,
      targetSetId: 55,
      targetSetType: 'Hercule Poirot',
      isTargetSetOwnedByMe: false,
      actionType: null,
    })).toBe(false);
  });

  it('rechaza si no es detective', () => {
    expect(canAddToDetectiveSet({
      selectedCardIds: [1],
      selectTypesCardIds: [['Another Victim', 1]],
      targetPlayerId: null,
      targetSecretId: null,
      targetCardId: null,
      targetSetId: 55,
      targetSetType: 'Hercule Poirot',
      isTargetSetOwnedByMe: true,
      actionType: null,
    })).toBe(false);
  });

  it('rechaza sin targetSetId', () => {
    expect(canAddToDetectiveSet({
      selectedCardIds: [1],
      selectTypesCardIds: [['Ariadne Oliver', 1]],
      targetPlayerId: null,
      targetSecretId: null,
      targetCardId: null,
      targetSetId: null,
      actionType: null,
    })).toBe(false);
  });
});
