import json
from pydantic import BaseModel
from typing import List
from pydantic.fields import FieldInfo
from typing import get_args, get_origin, Union
import inspect

# Importa tus modelos de la aplicación
from app.websockets.protocol.messages import AnyDetails
from app.websockets.protocol.events import WSEvent


def get_field_type_str(field: FieldInfo) -> str:
    """Función auxiliar para obtener una representación legible del tipo de un campo."""
    type_hint = field.annotation
    origin = get_origin(type_hint)

    if origin is Union:
        # Maneja tipos Optional[T], que son Union[T, None]
        args = get_args(type_hint)
        if len(args) == 2 and args[1] is type(None):
            return f"Optional[{args[0].__name__}]"

        # Maneja otras uniones si las tuvieras
        return " | ".join([arg.__name__ for arg in args])

    if origin is list or origin is List:
        # Maneja listas, ej: List[Card]
        list_type_args = get_args(type_hint)
        if list_type_args:
            return f"List[{list_type_args[0].__name__}]"
        return "List"

    if hasattr(type_hint, "__name__"):
        return type_hint.__name__

    return str(type_hint)


def generate_websocket_docs():
    """
    Genera un archivo MARKDOWN claro y legible con la documentación
    de todos los payloads de WebSocket, usando tablas.
    """
    payload_models = get_args(AnyDetails)

    with open("WEBSOCKET_API.md", "w", encoding="utf-8") as f:
        f.write("# 📖 Documentación de la API de WebSockets\n\n")
        f.write(
            "Esta es la lista de todos los posibles eventos que el servidor puede enviar a través de WebSockets.\n\n"
        )
        f.write("La estructura general de cada mensaje es:\n")
        f.write('```json\n{\n  "details": { ...payload... }\n}\n```\n\n')
        f.write("<br>\n\n")

        # Ordenar los eventos alfabéticamente por su nombre
        for model in sorted(
            payload_models, key=lambda m: m.model_fields["event"].default.value
        ):
            event_name = model.model_fields["event"].default

            f.write(f"--- \n\n")
            f.write(f"## Evento: `{event_name.value}`\n\n")

            if model.__doc__:
                description = " ".join(model.__doc__.strip().split())
                f.write(f"**Descripción:** {description}\n\n")

            f.write("**Payload (`details`):**\n\n")
            f.write("| Campo | Tipo | Descripción | Requerido |\n")
            f.write("|---|---|---|---|\n")

            for name, field in model.model_fields.items():
                if (
                    name == "event"
                ):  # Omitimos el campo 'event' que ya está en el título
                    continue

                field_type = get_field_type_str(field)
                description = field.description or " "
                is_required = "Sí" if field.is_required() else "No"

                f.write(
                    f"| `{name}` | `{field_type}` | {description} | {is_required} |\n"
                )

            f.write("\n")

    print("✅ Documentación mejorada generada en WEBSOCKET_API.md")


if __name__ == "__main__":
    generate_websocket_docs()
