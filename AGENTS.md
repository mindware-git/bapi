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

### Deploy
```
sudo nano /etc/nginx/sites-available/bapi

server {
    listen 80;
    server_name bapi.mindware.kr;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

sudo ln -s /etc/nginx/sites-available/bapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```