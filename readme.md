Project Structure
-----------------

server/
├── app/
│   ├── __init__.py            # Makes the app a Python package
│   ├── main.py                # FastAPI app initialization and lifespan management
│   ├── models/                # Pydantic schemas / ODM models
│   │   ├── __init__.py        # Marks the directory as a Python package
│   │   ├── user.py            # User model
│   ├── controllers/           # API route handlers (controllers)
│   │   ├── __init__.py        # Marks the directory as a Python package
│   │   ├── user_routes.py     # Routes for user-related operations
│   ├── services/              # Business logic layer
│   │   ├── __init__.py        # Marks the directory as a Python package
│   │   ├── user_service.py    # User-related business logic
│   ├── database/              # Database connection and helper functions
│   │   ├── __init__.py        # Marks the directory as a Python package
│   │   └── mongodb.py         # MongoDB connection setup
│   └── utils/                 # Utility functions (e.g., authentication helpers)
│       └── auth.py            # JWT or token validation logic
├── requirements.txt           # List of Python dependencies



## How to run the project

1. Create a virtual environment with Python and activate it.

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```


3. Run the FastAPI app:

```bash
uvicorn app.main:app --reload
```

or

```bash
python server.py
```


