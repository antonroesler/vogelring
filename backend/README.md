# Vogelring Backend

FastAPI backend for the Vogelring bird tracking application.

## Development

Install dependencies:
```bash
uv sync --extra test
```

Run tests:
```bash
uv run pytest
```

Run the application:
```bash
uv run uvicorn src.main:app --reload
```