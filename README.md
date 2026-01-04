# Real-Time Multiplayer Game Platform 🎮

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-17+-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org/)

**Full-stack multiplayer game engine** developed as a capstone Software Engineering project at FaMAF. The system implements a Service-Oriented Architecture (SOA) decoupling high-performance backend logic from a reactive frontend interface.

---

## 🚀 Key Engineering Features

### 📡 Real-Time Communication Architecture
Unlike traditional CRUD apps, this platform requires sub-100ms latency for game state synchronization.
* **Hybrid Protocol Strategy:**
    * **Client $\to$ Server:** HTTP REST API for transactional actions (Lobby creation, Joining games, playing cards).
    * **Server $\to$ Client:** **WebSockets** for broadcasting game state updates to all connected players in real-time.
* **Concurrency:** Leveraged Python's `asyncio` in FastAPI to handle multiple concurrent game lobbies without blocking I/O.

### ⚙️ Development Methodology (Agile/Scrum)
This project simulated a real-world engineering environment:
* **Sprints:** 3 Sprints of 2.5 weeks each.
* **Roles:** Rotated Product Owner and Scrum Master roles.
* **Tooling:** JIRA for ticket tracking (User Stories, Tasks, Bugs) and Estimations.
* **QA & CI:** Mandatory Code Reviews and Unit Testing coverage for acceptance criteria (Definition of Done).
* **Branching:** Strict Gitflow workflow (`master` -> `develop` -> `feature/`).

---

## 📂 Monorepo Structure

This repository consolidates the original microservices architecture for portfolio demonstration:

```bash
├── backend/          # FastAPI Application
│   ├── main.py       # Entry point & WebSocket manager
│   ├── models/       # Pydantic models & DB Schemas
│   └── routers/      # API Endpoints 
│
├── frontend/         # React SPA
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   └── contexts/    # WebSocket Context providers
