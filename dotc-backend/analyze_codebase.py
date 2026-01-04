import os
import io

# -----------------------------------------------------------------------------
# 1. Configuración
# -----------------------------------------------------------------------------

# Directorios a escanear: Incluimos la aplicación y las pruebas.
SCAN_DIRS = ["app", "tests"]

# Archivo de salida para el contexto del LLM
OUTPUT_FILE = "llm_context_data_complete.txt"

# Extensiones de archivo a incluir (código fuente y documentación)
INCLUDED_EXTENSIONS = (
    ".py",
    ".md",
    ".txt",
    ".ini",
    ".yaml",
    ".yml",
    ".json",
    "requirements.txt",
)

# Archivos o directorios a ignorar (artefactos de ejecución, caché, etc.)
EXCLUDED_PATHS = (
    "__pycache__",
    ".python-version",
    "htmlcov",  # Directorio de reportes de cobertura (pytest-cov)
    OUTPUT_FILE,
)

# -----------------------------------------------------------------------------
# 2. Funciones de ayuda
# -----------------------------------------------------------------------------


def analyze_file(filepath: str) -> str:
    """Lee el contenido de un archivo y lo formatea para el contexto del LLM."""
    try:
        with io.open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            # Truncamiento para evitar exceder la ventana de contexto del LLM
            MAX_LENGTH = 5000
            if len(content) > MAX_LENGTH:
                content = (
                    content[:MAX_LENGTH] + "\n... [CONTENIDO TRUNCADO] ..."
                )

        # Determinamos el tipo de sintaxis para el bloque de código
        if filepath.endswith(".py"):
            syntax = "python"
        elif filepath.endswith(".md"):
            syntax = "markdown"
        elif filepath.endswith((".yaml", ".yml", ".ini")):
            syntax = "yaml"  # O 'ini' / 'json' según corresponda
        else:
            syntax = ""

        # Formato de salida estructurado
        return (
            f"---FILE START---\n\n"
            f"## ARCHIVO: {filepath}\n\n"
            f"```{syntax}\n"
            f"{content.strip()}\n"
            f"```\n\n"
            f"---FILE END---\n\n"
        )
    except Exception as e:
        return f"## ARCHIVO: {filepath}\nERROR AL LEER: {e}\n\n"


def traverse_and_collect_content(scan_dirs: list) -> str:
    """Recorre la lista de directorios especificada y concatena el contenido."""
    print(f"Iniciando análisis de directorios: {scan_dirs}")
    full_context = ""
    file_count = 0

    for root_dir in scan_dirs:
        if not os.path.isdir(root_dir):
            print(f"Advertencia: Directorio no encontrado: {root_dir}")
            continue

        for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
            # Filtrar directorios a excluir
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_PATHS]

            for filename in filenames:
                if (
                    filename.endswith(INCLUDED_EXTENSIONS)
                    or filename in INCLUDED_EXTENSIONS
                ) and filename not in EXCLUDED_PATHS:
                    filepath = os.path.join(dirpath, filename)
                    full_context += analyze_file(filepath)
                    file_count += 1
                    print(f"  Analizado: {filepath}")

    print(f"\nAnálisis completado. {file_count} archivos procesados.")
    return full_context


# -----------------------------------------------------------------------------
# 3. Ejecución principal
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    context = traverse_and_collect_content(SCAN_DIRS)

    # Encabezado para contextualizar al LLM sobre la estructura y la calidad
    header = (
        f"# CONTEXTO COMPLETO DE INGENIERÍA DE SOFTWARE - PROYECTO BACKEND\n\n"
        f"Este contexto incluye tanto el código de la aplicación (`app/`) como los Unit Tests y Tests de Integración (`tests/`).\n"
        f"La inclusión de tests es fundamental para evaluar la **Calidad (C&P)** del software, la **Correctitud** (el programa se comporta según especificaciones), y la **Testeabilidad** de la arquitectura.\n"
        f"Los tests son la evidencia de que el código cumple con la definición de **DONE** (que requiere Unit Tests completos: casos base, éxito, errores y corner cases) [3, 4].\n"
        f"----------------------------------------------------------------\n\n"
    )

    final_output = header + context

    # Escribir el resultado final.
    with io.open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_output)

    print(f"\nResultado guardado en: {OUTPUT_FILE}")
    print(
        "Este archivo incluye ahora el código de aplicación y la validación (tests)."
    )
