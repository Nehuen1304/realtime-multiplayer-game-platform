# Revisión arquitectónica: por qué, beneficios y ejemplos prácticos

Esta guía prioriza cambios con máximo beneficio por esfuerzo. Incluye el “por qué”, el impacto esperado y ejemplos mínimos Antes/Después aplicados a tu código actual.

## 1) Arreglar defaults mutables en modelos de dominio (máximo ROI, mínimo esfuerzo)

Por qué

- En Pydantic (y Python), usar `lista = []` como default comparte la misma lista entre instancias, generando fugas de estado (bugs difíciles de detectar al crear múltiples partidas o jugadores).
- Rompe el principio de aislamiento del dominio y puede “contaminar” pruebas.

Antes (riesgoso)

```py
# app/domain/models.py
class PlayerInGame(BaseModel):
    hand: List[Card] = []
    secrets: List[SecretCard] = []

class Game(BaseModel):
    players: List[PlayerInGame] = []
    deck: List[Card] = []
    discard_pile: List[Card] = []
    draft: List[Card] = []
```

Después (seguro) — misma API pública

```py
from pydantic import Field
class PlayerInGame(BaseModel):
    hand: List[Card] = Field(default_factory=list)
    secrets: List[SecretCard] = Field(default_factory=list)

class Game(BaseModel):
    players: List[PlayerInGame] = Field(default_factory=list)
    deck: List[Card] = Field(default_factory=list)
    discard_pile: List[Card] = Field(default_factory=list)
    draft: List[Card] = Field(default_factory=list)
```

Beneficio

- Elimina un bug de estado compartido con 1–2 líneas por clase; impacto alto en confiabilidad.

---

## 2) Desacoplar el core de la API (Clean Architecture / Ports & Adapters)

Por qué

- Si el core (servicios/manager) importa `app/api/schemas`, queda acoplado a transporte HTTP (Pydantic); dificulta reutilizar lógica (WS, CLI, jobs) y testear sin FastAPI.
- Separar “Casos de Uso” (Application Core) de “Adaptadores” (FastAPI/WebSocket) reduce fricción de cambios y favorece SOLID (DIP).

Antes (acoplado a HTTP)

```py
# app/game/game_manager.py
from ..api.schemas import CreateGameRequest, CreateGameResponse
async def create_game(self, request: CreateGameRequest) -> CreateGameResponse:
    return await self.lobby_service.create_game(request)
```

Después (core puro + mapping en la API)

```py
# app/game/use_cases/create_game.py (Core)
from dataclasses import dataclass
@dataclass
class CreateGameCommand:
    host_id: int; name: str; min_players: int; max_players: int; password: str | None = None
@dataclass
class CreateGameResult:
    game_id: int
class CreateGameUseCase:
    def __init__(self, commands, queries):
        self.commands, self.queries = commands, queries
    async def __call__(self, cmd: CreateGameCommand) -> CreateGameResult:
        gid = self.commands.create_game(cmd.name, cmd.min_players, cmd.max_players, cmd.host_id, cmd.password)
        return CreateGameResult(game_id=gid)

# app/api/endpoints.py (Adapter HTTP)
@router.post("/games", response_model=CreateGameResponse)
async def create_game(req: CreateGameRequest, use_case: CreateGameUseCase = Depends(...)):
    cmd = CreateGameCommand(req.host_id, req.game_name, req.min_players, req.max_players, req.password)
    res = await use_case(cmd)
    return CreateGameResponse(game_id=res.game_id)
```

Beneficio

- Tests del core sin FastAPI/Pydantic; puedes exponer lo mismo por WS o tareas sin tocar el dominio.

---

## 3) Unit of Work (UoW) por caso de uso (consistencia transaccional)

Por qué

- Hoy `DatabaseCommandManager` hace `commit()` por método; si un caso de uso hace varias escrituras y falla a la mitad, quedan commits parciales.
- UoW agrupa una operación de aplicación en una única transacción: o todo o nada.

Implementación mínima

```py
# app/database/uow.py
class IUnitOfWork:
    def __enter__(self): ...
    def __exit__(self, exc_type, exc, tb): ...
    def commit(self): ...

class SqlAlchemyUoW(IUnitOfWork):
    def __init__(self, session_factory): self._sf = session_factory
    def __enter__(self):
        self.session = self._sf()
        self.queries = QueryManager(self.session)
        self.commands = CommandManager(self.session)  # versión sin commit interno
        return self
    def __exit__(self, t, e, tb):
        if e: self.session.rollback()
        self.session.close()
    def commit(self): self.session.commit()
```

Uso en caso de uso

```py
class StartGameUseCase:
    def __init__(self, uow: IUnitOfWork, notifier):
        self.uow, self.notifier = uow, notifier
    async def __call__(self, cmd):
        with self.uow as uow:
            # varias escrituras…
            # uow.commands.update_game_status(...)
            # uow.commands.create_deck_for_game(...)
            uow.commit()  # un solo commit al final
        await self.notifier.notify_game_started(...)
```

Beneficio

- Atomicidad real; simplifica recuperación ante errores; alinea responsabilidades (Commands no deciden cuándo confirmar).

---

## 4) Notificator desacoplado de DTOs de API (frontera estable)

Por qué

- `Notificator` hoy importa `app/api/schemas` (p. ej. `GameLobbyInfo`), acoplando core a la forma HTTP.
- Un DTO de aplicación (p. ej. `LobbyGameSummary`) estabiliza el core; los adaptadores mapean a lo que necesite cada protocolo.

Después

```py
# app/game/dto.py
from dataclasses import dataclass
@dataclass
class LobbyGameSummary:
    id: int; name: str; min_players: int; max_players: int
    host_id: int; player_count: int; password: str | None; status: str

# app/game/helpers/notificators.py
async def notify_game_created(self, game: LobbyGameSummary): ...

# app/api/mappers.py
def to_api_game_lobby_info(x: LobbyGameSummary) -> GameLobbyInfo: ...
```

Beneficio

- Core independiente de Pydantic/HTTP; WS y HTTP pueden evolucionar sin tocar el núcleo.

---

## 5) Plugin/Registry para efectos (Open/Closed)

Por qué

- `EffectExecutor` concentra un mapa grande de efectos; cada efecto nuevo requiere editarlo (cerrado al cambio).
- Un registro inyectable permite alta/baja de efectos por configuración o pruebas, cumpliendo OCP.

Después (idea)

```py
class IEffectRegistry:
    def get_event_effect(self, card_type): ...
    def get_set_effect(self, counter): ...

class DictEffectRegistry(IEffectRegistry):
    def __init__(self, event_map, set_map): self.event_map, self.set_map = event_map, set_map
    def get_event_effect(self, t): return self.event_map.get(t)
    def get_set_effect(self, c): return self.set_map.get_matching_effect(c)

class EffectExecutor:
    def __init__(self, queries, commands, notifier, registry: IEffectRegistry):
        self.read, self.write, self.notifier, self.registry = queries, commands, notifier, registry
    def classify_effect(self, played_cards):
        if len(played_cards) == 1:
            return self.registry.get_event_effect(played_cards[0].card_type)
        from collections import Counter
        return self.registry.get_set_effect(Counter(c.card_type for c in played_cards))
```

Beneficio

- Extensibilidad sin tocar el ejecutor; tests más sencillos (inyectas un registro fake).

---

## 6) Domain Events / Event Bus (opcional, evolutivo)

Por qué

- Evita que casos de uso llamen explícitamente a WS/Email/Logs; los efectos secundarios se suscriben a eventos.
- Mejora testeabilidad (core emite eventos, los handlers se prueban aparte).

Ejemplo

```py
@dataclass
class GameCreated: game_id: int

class InMemoryEventBus:
    def __init__(self): self._h = {}
    def subscribe(self, t, f): self._h.setdefault(t, []).append(f)
    async def publish(self, e):
        for f in self._h.get(type(e), []): await f(e)
```

Beneficio

- Menos acoplamiento; puedes añadir/retirar notificaciones sin tocar el core.

---

## 7) Migraciones (Alembic) vs `Base.metadata.create_all` en runtime

Por qué

- `create_all` en producción impide versionar el esquema; no hay rollback ni trazabilidad.
- Alembic registra cambios de esquema reproducibles entre entornos (dev/test/prod).

Pasos

- `alembic init alembic` → configurar `target_metadata = Base.metadata`.
- `alembic revision --autogenerate -m "init"` → `alembic upgrade head`.
- Quitar `Base.metadata.create_all(...)` de `app/main.py`.

Beneficio

- Seguridad operativa y CI/CD más confiable; cambios de DB auditables y reversibles.

---

## 8) Settings por ambiente (pydantic-settings)

Por qué

- Centraliza configuración (DB URL, CORS, etc.), valida tipos, permite `.env` por ambiente.

Ejemplo

```py
# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DOTC_")
    database_url: str
    cors_origins: list[str] = ["*"]
settings = Settings()

# app/main.py
middleware = [Middleware(CORSMiddleware, allow_origins=settings.cors_origins, ...)]
```

Beneficio

- Menos “magia” en el código; ambientes bien definidos.

---

## 9) Mapear enums a primitivos en infraestructura

Por qué

- Persistir/serializar enums como strings/ints en los adapters evita acoplar consumidores a tus tipos Python; facilita integración y cambios internos.

Ejemplo (mapper ORM ↔ dominio)

```py
# al leer de DB
role = PlayerRole(db_row.role_str)
# al persistir
row.role_str = role.value
```

Beneficio

- Infraestructura estable ante cambios internos del dominio; compatibilidad hacia afuera.

---

## 10) Repositorios por agregado (cuando crezca el dominio)

Por qué

- Clarifica límites de consistencia (Game/Player como agregados) y encapsula invariantes de persistencia.

Interfaces mínimas

```py
class IGameRepository:
    def get(self, game_id: int) -> Game | None: ...
    def save(self, game: Game) -> None: ...
```

Beneficio

- Mejor expresividad y pruebas; separación clara entre estado del agregado y detalles ORM.

---

## 11) Logging y errores

Por qué

- `print(...)` no es observable ni estructurado; `logging` con niveles permite diagnosticar en producción y filtrar en tests.

Ejemplo

```py
import logging
logger = logging.getLogger(__name__)
try:
    ...
except Exception:
    logger.exception("Fallo al crear partida")
    raise
```

---

## 12) Testing (contratos y core)

Enfoque

- Dominio puro (entidades/servicios) sin frameworks.
- Casos de uso con UoW en memoria/fake.
- Contratos de puertos (ICommandManager/IQueryManager/IConnectionManager) con fakes para garantizar expectativas.
- Mappers: ORM↔Dominio y Dominio↔API.

Beneficio

- Confianza al refactorizar; pruebas rápidas y aisladas.

---

## Roadmap sugerido (incremental y pragmático)

1) Defaults mutables → `Field(default_factory=list)`.
2) 2–3 casos de uso clave como comandos/queries (create/join/start) + mapeo en endpoints.
3) UoW: un solo `commit()` por caso de uso; Commands sin `commit()` interno.
4) Notificator recibe DTOs de aplicación (no API); agregar mapper en capa API.
5) (Si necesitas extensibilidad) EffectRegistry inyectable.
6) Alembic + settings por ambiente cuando estabilice el esquema.

Con estos pasos obtienes: core testeable y estable, transporte desacoplado, transacciones consistentes y menor fricción para crecer o cambiar interfaces sin romper el dominio.
