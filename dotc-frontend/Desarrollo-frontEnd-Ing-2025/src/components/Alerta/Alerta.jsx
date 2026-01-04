// En Alerta.jsx
import { useEffect } from "react";
import "./AlertaStyle.css";
import { Button } from "../Button/Button";
// 1. Aceptamos 'titulo' en los props
export function Alerta({
  tipo = "info",
  titulo, // <-- AÑADIR ESTE PROP
  mensaje,
  onClose,
  duracion = 3000,
}) {
  // ... (el useEffect se queda igual)

  // 2. Mantenemos la lógica actual como 'default'
  const getTituloDefault = () => {
    switch (tipo) {
      case "success": return "✅ Éxito";
      case "error": return "❌ Error";
      case "warning": return "⚠️ Advertencia";
      default: return "ℹ️ Información";
    }
  };

  // 3. Decidimos cuál título mostrar
  const displayTitulo = titulo || getTituloDefault();

  return (
    <div className="alerta-overlay">
      {/* 4. Usamos el título decidido */}
      <div className={`alerta-modal alerta-${tipo}`}>
        <h3 className="alerta-titulo">{displayTitulo}</h3>
        {/* ... (el resto del componente se queda igual) */}
        <p className="alerta-mensaje">{mensaje}</p>
        <div className="alerta-botones">
          <Button variant="primary" onClick={onClose}>
            Aceptar
          </Button>
        </div>
      </div>
    </div>
  );
}