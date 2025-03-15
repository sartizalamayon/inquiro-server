from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers.user_routes import router as user_router
from app.database.mongodb import lifespan
from app.controllers.paper_routes import router as paper_router

# Initialize FastAPI app with lifespan
app = FastAPI(title="inquiro", lifespan=lifespan)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user_router)
app.include_router(paper_router)

@app.get("/")
async def root():
    return {"message": "Welcome to inquiro server!"}