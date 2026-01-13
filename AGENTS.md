# AGENTS.md

## Backend (FastAPI)

The backend is a [FastAPI](https://fastapi.tiangolo.com/) application.

### Setup
- **Install dependencies:** `uv sync`

### Database Setup
- **Initialize database with sample data:** `uv run python -m app.seed_data`
  - This command creates the database tables and populates them with sample
  - Run this before starting the server for the first time

### Development
- **Start dev server:** `uv run fastapi dev`
  - The server will be available at [http://localhost:8000](http://localhost:8000).
- **production server start:** `uv run uvicorn app.main:app --reload`
  - The server will be available at [http://localhost:8000](http://localhost:8000).

### Testing
- **Run tests:** `uv run pytest`
