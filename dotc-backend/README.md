# Death on the Cards - Backend

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Comms](https://img.shields.io/badge/Comms-WebSockets-purple.svg)](https://websocket.org/)
[![ORM](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/Tests-Pytest-informational.svg)](https://docs.pytest.org/)

Desarrollo backend del proyecto **"Death on the Cards"** para el laboratorio de la materia Ingeniería de Software I 2025 - FAMAF - UNC.

Este servidor gestiona toda la lógica de negocio, la comunicación en tiempo real y la persistencia de datos para la adaptación del juego de mesa homónimo.

## 🏛️ Arquitectura del proyecto

El sistema está diseñado en capas y módulos con responsabilidades únicas, siguiendo los principios de alta cohesión y bajo acoplamiento:

- **Interfaces (`api`, `websockets`):** Comunicación en tiempo real, utilizando endpoints claros, siguiendo un protocolo definido, y permitiendo notificaciones para clientes individuales, de una partida en especifíco o del lobby general.
- **Dominio (`domain`):** Define las entidades centrales del sistema.
- **Lógica de Aplicación (`game`):** Implementa las reglas y flujos del juego, gestionando el estado de las partidas y la interacción entre jugadores.
- **Acceso a Datos (`database`):** Separación de la responsabilidad de comandos (escritura) y consultas (lectura).
- **Inyección de Dependencias (`dependencies`):** Facilita el testing, la mantenibilidad y el bajo acoplamiento.

### Estructura de capas

<pre>
<code>
<a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app">/app</a>
│
├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/main.py">main.py</a>
│
├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/api">api/</a>                    # (1. Capa de interfaz API REST)
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/api/endpoints">endpoints/</a>          # (Rutas: /games, /players)
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/api/exception_handlers.py">exception_handlers.py</a>
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/api/router.py">router.py</a>
│   └── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/api/schemas.py">schemas.py</a>
│
├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/websockets">websockets/</a>             # (1. Capa de interfaz Websocket)
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/websockets/connection_manager.py">connection_manager.py</a>
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/websockets/interfaces.py">interfaces.py</a>
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/websockets/router.py">router.py</a>
│   └── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/websockets/protocol">protocol/</a>           # (Eventos, mensajes y detalles)
│
├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/domain">domain/</a>                 # (2. Capa de dominio)
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/domain/models.py">models.py</a>
│   └── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/domain/enums.py">enums.py</a>
│
├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/game">game/</a>                   # (3. Capa de lógica de aplicación)
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/game/exceptions.py">exceptions.py</a>
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/game/effect_executor.py">effect_executor.py</a>
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/game/game_manager.py">game_manager.py</a>
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/game/interfaces.py">interfaces.py</a>
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/game/services">services/</a>           # (Servicios especializados: lobby, setup, turno, etc.)
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/game/effects">effects/</a>            # (Efectos de sets y de eventos)
│   └── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/game/helpers">helpers/</a>            # (Utilidades reutilizables: validadores, notificadores)
│
├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/database">database/</a>               # (4. Capa de persistencia de datos)
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/database/orm_models.py">orm_models.py</a>
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/database/interfaces.py">interfaces.py</a>
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/database/queries.py">queries.py</a>
│   ├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/database/commands.py">commands.py</a>
│   └── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/database/mappers.py">mappers.py</a>
│
├── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/dependencies">dependencies/</a>           # (Mecanismo de inyección de dependencias)
│   └── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/blob/master/app/dependencies/dependencies.py">dependencies.py</a>
│
└── <a href="https://github.com/IngSoft1-Bobina/dotc-backend/tree/master/app/tests">tests/</a>                  # (Batería de tests sobre las capas anteriores)
</code>
</pre>

## 🚀 Configuración y ejecución

Sigue estos pasos para levantar el entorno de desarrollo local:

### 1. Prerrequisitos

- Python 3.10+
- `uv`: Un instalador y gestor de paquetes de Python. Si no lo tienes, instálalo con `pip install uv` o tu administrador de paquetes del SO.

### 2. Instalación

1. **Clona el repositorio:**

    ```bash
    git clone https://github.com/IngSoft1-Bobina/dotc-backend.git
    cd dotc-backend
    ```

2. **Crea el entorno virtual:**

    ```bash
    uv venv
    ```

3. **Activa el entorno virtual:**
    - En Linux / macOS:

      ```bash
      source .venv/bin/activate
      ```

    - En Windows (PowerShell):

      ```bash
      .venv\Scripts\Activate.ps1
      ```

4. **Instala las dependencias:**

    ```bash
    uv pip install -r requirements.txt
    ```

### 3. Ejecución

1. **Inicia el servidor de desarrollo:**
    El flag `--reload` reiniciará el servidor automáticamente cada vez que guardes un cambio en el código.

    ```bash
    uv run uvicorn app.main:app --reload
    ```

2. **Accede a la documentación de la API:**
    Una vez que el servidor esté corriendo, FastAPI genera automáticamente una documentación interactiva. Abre en tu navegador:
    [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## ✅ Ejecución de tests

Para asegurar que la lógica de negocio y las operaciones de base de datos funcionan correctamente, ejecuta la suite de tests con `pytest`.

El flag `--cov=app` permite visualizar el *coverage* que tienen los tests implementados por sobre la aplicación.

```bash
uv run pytest tests/ --cov=app
```
