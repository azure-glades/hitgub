# CornHub
where repositories are kernels on a corn cob. Better than github fr fr

Structure:
```
repo-manager/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic models (your DTOs)
│   ├── crud.py          # DB operations (your @Repository)
│   ├── dependencies.py  # DI containers, auth logic
│   └── git_ops.py       # GitPython wrapper
├── requirements.txt
└── .env
```

Start app with:
```
uvicorn app.main:app --reload --port 8080
```

Visit http://localhost:8080/docs to vie* endpoints