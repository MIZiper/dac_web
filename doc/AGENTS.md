# AGENTS.md — DAC Web Project Knowledge

## Overview

DAC Web is a browser-based data analysis application using the DAC (Data Action Context) framework. Users create analysis sessions, configure data/action nodes in contexts, run actions, and visualize results via matplotlib. The app is containerized with Docker/Podman.

## Architecture

```
Browser (SPA) ──→ FastAPI backend (:8000) ──→ per-session subprocess (random port)
                          │                           │
                    PostgreSQL (nodes, histories)    matplotlib WebAgg
```

- **Frontend**: Svelte 5 SPA served as static files by FastAPI in production
- **Backend**: FastAPI manages sessions, proxies `/app/*` to session subprocesses
- **Sessions**: Each analysis session is a Python subprocess (`dac_web.app.entry`), isolated by UUID
- **Storage**: PostgreSQL (`nodes` table for projects, `histories` for inheritance), or flat JSON files if DB unavailable. The old `publishes` table is deprecated; publication/status is owned by an external TC system.

## Directory Layout

```
/home/pi/dac_web/
├── AGENTS.md                          # this file
├── Dockerfile                         # 2-stage: Node build + Python runtime
├── README.md
├── doc/GOALS.md                       # project goals (Chinese)
├── backend/
│   ├── pyproject.toml                 # Python deps: fastapi, asyncpg, httpx, matplotlib, miz-dac
│   └── dac_web/
│       ├── main.py                    # FastAPI app, lifespan, route mounts
│       ├── schema.py                  # Pydantic models (request/response)
│       ├── webagg_starlette.py        # matplotlib WebAgg server (Starlette)
│       ├── api/
│       │   ├── handler.py             # /api routes: session CRUD, project list/save
│       │   └── rev_proxy.py           # reverse proxy /app/* → subprocess (HTTP+SSE+WS)
│       ├── app/
│       │   ├── entry.py               # subprocess entry point (prints port to stdout)
│       │   └── handler.py             # DAC framework routes: data/context/action CRUD
│       └── db/
│           ├── connection.py          # asyncpg pool, get_db() dependency
│           └── schema.sql             # tables: nodes, histories (publishes deprecated)
├── dac-frontend/                      # PRIMARY frontend (Svelte 5)
│   ├── package.json                   # deps: svelte, @sveltestrap/sveltestrap, sv-router, axios
│   ├── vite.config.ts                 # proxies /api, /app, /api/mpl to backend
│   └── src/
│       ├── main.ts                    # mount point
│       ├── App.svelte                 # root layout: Navbar + Router
│       ├── app.css                    # global styles
│       ├── router.ts                  # sv-router hash routes
│       ├── schema.d.ts                # TS interfaces mirroring backend models
│       ├── pages/
│       │   ├── HomePage.svelte        # project list with pagination, tabs (All/Published)
│       │   ├── MainPage.svelte        # main analysis workspace (413 lines)
│       │   └── MainPageHandler.svelte.ts  # reactive state ($state) + all API handlers
│       ├── lib/                       # reusable components
│       │   ├── ContextList.svelte     # context dropdown with CRUD
│       │   ├── DataList.svelte        # tree data browser
│       │   ├── ActionList.svelte      # action list with status icons
│       │   ├── YamlEditor.svelte      # CodeMirror YAML editor
│       │   ├── MplCanvas.svelte       # matplotlib WebAgg canvas
│       │   ├── ScenarioList.svelte    # navbar scenario selector
│       │   ├── DataNode.svelte        # recursive tree node
│       │   ├── SaveProjectDropdown.svelte  # navbar save / save as
│       │   └── StatsTable.svelte      # modal stats table
│       ├── tasks/
│       │   ├── TaskRouter.svelte.ts   # action_type → modal component mapping
│       │   └── NameEditor.svelte      # example task modal
│       └── utils/
│           ├── FetchObjects.ts        # axios instances (ax_api, ax_app), constants
│           └── NavibarSnippet.svelte.ts  # teleported navbar slot (reactive snippet)
├── frontend/                          # LEGACY Vue 3 + Vuetify frontend
├── storage/
│   ├── projects/                      # active project .json files
│   ├── projects_save/                 # legacy published/shared project files
│   └── logs/                          # session output logs
└── test/
```

## Key Patterns

### Svelte 5 Reactivity
- No Svelte stores — uses `$state`, `$derived`, `$effect`, `$props` runes
- Global app state in `MainPageHandler.svelte.ts`: `export const appdata = $state({...})`
- Navbar teleport: `navTeleport.snippet = mySnippet` in `NavibarSnippet.svelte.ts`

### Session Lifecycle
1. `POST /api/new` → creates subprocess, returns `sess_id`, `project_id: null`
2. `POST /api/load` → loads existing project into subprocess, returns `sess_id`
3. `POST /api/term` → kills subprocess, removes from `user_manager`
4. `POST /api/save` → saves config to DB/file; signature mismatch creates new node with inheritance

### API Client
- `ax_api` = `/api` prefix (session management)
- `ax_app` = `/app` prefix (proxied to subprocess for data/context/action CRUD)
- `SESSID_KEY = "dac-sess_id"` — set as header on all requests after session creation

### Database
- **`nodes`**: `id UUID`, `content JSONB`, `creator_signature VARCHAR(20)`, `valid BOOLEAN`
- **`histories`**: tracks inheritance chain (`node_id` → `inherit_from_id`)
- **`publishes`**: deprecated; status is now read from the linked external system
- Config stored as `{"dac": {...}, "dac_web": {"version": ..., "signature": ...}}`

### Routes (sv-router hash-based)
| Path | Component | Purpose |
|------|-----------|---------|
| `/#/` | HomePage | Project list |
| `/#/projects/new` | MainPage | New analysis session |
| `/#/projects/:id` | MainPage | Load existing project |
| `/#/dev-test` | YamlEditor | Standalone YAML editor |

## Important Conventions

- **DO NOT expose `creator_signature`** — it's a password-like field, never display or return to frontend
- Session termination: `onDestroy` of MainPage calls `/api/term` via `cleanupAnalysis`; `beforeunload` is fallback for tab close
- All API handlers use `try/catch` → set `appdata.errorMessage` → Toast displayed via `$effect`
- YAML serialization uses the `yaml` npm package; error messages shown in Toast
- SSE is used for action execution progress (events: `started`, `progress`, `stats`, `completed`, `message`)

## Commands

```bash
# Frontend dev
cd dac-frontend && pnpm dev

# Frontend typecheck
cd dac-frontend && npx svelte-check --tsconfig ./tsconfig.app.json

# Frontend build
cd dac-frontend && pnpm build

# Backend run
cd backend && uv run uvicorn dac_web.main:app --host 0.0.0.0 --port 8000
# Local VS Code tasks use fixed ports: PostgreSQL 5431, backend 8031, frontend 5131.

# Docker build
podman build -t dac_web .
```

## Notes for Agents

- **Python is in `.venv`**: always use `backend/.venv/bin/python` or `uv run python`
- **Node is via pnpm**: `dac-frontend/` uses pnpm lockfile
- The legacy `frontend/` directory (Vue 3) should be ignored unless explicitly asked
- Backend supports dual storage (DB or JSON files) controlled by `DBSTORE` env var
- `creator_signature` is sensitive — strip from API responses and never display in UI
- The `/app` routes in `main.py` use `app.handler.router` only for `/docs`; actual traffic goes through `rev_proxy`
