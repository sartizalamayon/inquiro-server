Project Structure
-----------------

my_project/
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
└── .env                     # Environment variables (MONGODB_URI, DB_NAME, JWT_SECRET_KEY, etc.)

