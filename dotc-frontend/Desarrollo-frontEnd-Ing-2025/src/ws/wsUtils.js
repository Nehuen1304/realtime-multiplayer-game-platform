export function normalizeWsMessage(raw) {
  let msg;
  try {
    msg = typeof raw === "string" ? JSON.parse(raw) : raw;
  } catch {
    return { event: null, payload: null, raw };
  }
  // Soporta ambos formatos: {event, payload} o {details: {event, ...}}
  if (msg.event) {
    return { event: msg.event, payload: msg.payload ?? msg.details ?? {}, raw: msg };
  }
  if (msg.details && msg.details.event) {
    // El evento está anidado en details
    const { event, ...rest } = msg.details;
    return { event, payload: rest, raw: msg };
  }
  return { event: null, payload: msg, raw: msg };
}