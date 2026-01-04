import { describe, it, expect } from 'vitest';
import { normalizeWsMessage } from './wsUtils.js';

describe('normalizeWsMessage', () => {
  it('parses JSON string messages', () => {
    const raw = JSON.stringify({ event: 'TEST', payload: { a: 1 } });
    const res = normalizeWsMessage(raw);
    expect(res.event).toBe('TEST');
    expect(res.payload).toEqual({ a: 1 });
    expect(res.raw).toBeTypeOf('object');
  });

  it('returns null event on invalid JSON', () => {
    const res = normalizeWsMessage('{invalid-json');
    expect(res).toEqual({ event: null, payload: null, raw: '{invalid-json' });
  });

  it('supports direct object with event/payload', () => {
    const input = { event: 'E', payload: { x: 2 }, other: 'ignored' };
    const res = normalizeWsMessage(input);
    expect(res.event).toBe('E');
    expect(res.payload).toEqual({ x: 2 });
    expect(res.raw).toBe(input);
  });

  it('supports nested details format', () => {
    const input = { details: { event: 'NESTED', foo: 'bar', num: 3 } };
    const res = normalizeWsMessage(input);
    expect(res.event).toBe('NESTED');
    expect(res.payload).toEqual({ foo: 'bar', num: 3 });
  });

  it('falls back to payload being the message when no event present', () => {
    const input = { hello: 'world' };
    const res = normalizeWsMessage(input);
    expect(res.event).toBeNull();
    expect(res.payload).toEqual(input);
  });
});
