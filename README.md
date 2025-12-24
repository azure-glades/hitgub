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

## Some renames:
schemas.py -> json_dto.py
databases.py -> database_sessions.py
dependencies.py -> dependency_injector.py

## nonsense
main.py has api endpoints. based on endpoint it calls business logic functions which are in crud.py
crud.py does operations on pSQL, MongoDB databases. crud.py also calls git_ops.py which does git operations.

main.py sends info to crud.py using json data transfer objects (DTOs) who's schemas are in schemas.py
dependency injection into crud.py is done using dependencies.py
models.py has all the tables as objects/models

to add:


