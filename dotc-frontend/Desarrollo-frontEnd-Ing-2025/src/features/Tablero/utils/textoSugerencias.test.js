import { describe, it, expect } from 'vitest';
import { getDetectivePrincipal, getEvetoText, getDetectiveText, getEventoText } from './textoSugerencias.js';

describe('textoSugerencias utilities', () => {
  it('getDetectivePrincipal Harley-only', () => {
    expect(getDetectivePrincipal([['Harley Quin', 1]])).toBe('Harley Quin');
  });

  it('getDetectivePrincipal Mr Satterthwaite + Harley only => combo', () => {
    expect(getDetectivePrincipal([['Mr Satterthwaite', 1], ['Harley Quin', 2]])).toBe('Mr Satterthwaite y Harley Quin');
  });

  it('getDetectivePrincipal Satterthwaite + Harley + Marple => first non-Harley (Satterthwaite)', () => {
    const p = getDetectivePrincipal([
      ['Mr Satterthwaite', 1],
      ['Harley Quin', 2],
      ['Miss Marple', 3],
    ]);
    expect(p).toBe('Mr Satterthwaite'); // no combo porque hay otro tipo
  });

  it('getDetectivePrincipal Tommy + Tuppence => combo hermanos', () => {
    expect(getDetectivePrincipal([
      ['Tommy Beresford', 1],
      ['Tuppence Beresford', 2],
    ])).toBe('Tommy y Tuppence Beresford');
  });

  it('getDetectivePrincipal default single', () => {
    expect(getDetectivePrincipal([['Ariadne Oliver', 7]])).toBe('Ariadne Oliver');
  });

  it('getEvetoText known event', () => {
    expect(getEvetoText('Card trade')).toMatch(/intercambiar/i);
  });

  it('getEvetoText default', () => {
    expect(getEvetoText('__x')).toMatch(/evento/i);
  });

  it('getDetectiveText Parker Pyne', () => {
    expect(getDetectiveText('Parker Pyne')).toMatch(/ocultar/i);
  });

  it('getEventoText Cards off the table', () => {
    expect(getEventoText('Cards off the table')).toMatch(/descartar todas las cartas Not So Fast/i);
  });

  it('getEventoText default', () => {
    expect(getEventoText('__x')).toMatch(/evento/i);
  });
});