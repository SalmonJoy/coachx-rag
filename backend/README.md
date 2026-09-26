# Contextual Vector API

This is the FastAPI backend scaffold for the Contextual Vector RAG demo.

## Run

From the workspace root:

```powershell
C:\Users\salmo\AppData\Local\Programs\Python\Python311\python.exe -m uvicorn backend.app.main:app --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

## Endpoints

- `GET /` - app metadata and status.
- `GET /health` - health check.

## Check

```powershell
C:\Users\salmo\AppData\Local\Programs\Python\Python311\python.exe -m py_compile backend\app\main.py backend\app\api\routes.py backend\app\core\config.py
```
