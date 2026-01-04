// src/ws/wsManager.js
import { normalizeWsMessage } from "./wsUtils.js";

export class WSManager {
  constructor(url, handlers, context) {
    this.url = url;
    this.handlers = handlers;
    this.context = context;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.shouldReconnect = true; // Por defecto, intentamos reconectar
    this.connect();
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      console.log("⚠️ WebSocket ya está conectado o conectándose.");
      return;
    }

    this.shouldReconnect = true; // Permitir reconexión en nuevos intentos
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log(`✅ WebSocket (${this.context}) conectado a ${this.url}`);
    };

    this.ws.onmessage = (event) => {
      console.log(`📨 WebSocket (${this.context}) mensaje recibido:`, event.data);
      try {
        console.log("🔍 Normalizando mensaje WS...");
        const { event: eventType, payload, raw } = normalizeWsMessage(event.data);
        if (eventType && this.handlers[eventType]) {
          this.handlers[eventType](payload, this.context, this);
        } else {
          if (eventType) {
            console.warn(`🤷‍♂️ No se encontró un handler para el evento "${eventType}" en el contexto "${this.context}". Payload:`, raw);
          } else {
            console.warn(`❓ Mensaje WS recibido sin un tipo de evento en el contexto "${this.context}". Mensaje completo:`, raw);
          }
        }
      } catch (error) {
        console.error(`❌ Error al manejar mensaje WS (${this.context}):`, error, event.data);
      }
    };

    this.ws.onclose = (event) => {
      // El código 1000 significa que el cierre fue normal e intencionado.
      if (event.code === 1000 || !this.shouldReconnect) {
        console.log(`🔌 WebSocket (${this.context}) cerrado intencionadamente.`);
        return;
      }

      console.warn(`🔌 WebSocket (${this.context}) cerrado inesperadamente. Código: ${event.code}. Intentando reconectar...`);
      
      // Lógica de reconexión con exponential backoff
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000); // Max 30s
      setTimeout(() => {
        this.reconnectAttempts++;
        console.log(`🔄 Intento de reconexión #${this.reconnectAttempts} para ${this.context}...`);
        this.connect();
      }, delay);
    };

    this.ws.onerror = (error) => {
      console.error(`❌ WebSocket (${this.context}) error. Esto probablemente será seguido por un evento 'onclose'.`, error);
    };
  }

  send(eventType, payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ event: eventType, details: payload }));
    } else {
      console.warn(`WS (${this.context}) no está abierto. No se envió`, eventType, payload);
    }
  }

  close() {
    this.shouldReconnect = false; // Prevenir la reconexión automática
    if (this.ws) {
      try { this.ws.close(1000, "Cierre solicitado por el cliente"); } catch { }
    }
    this.ws = null;
  }
}
