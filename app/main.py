from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers.user_routes import router as user_router
from app.database.mongodb import lifespan
from app.controllers.paper_routes import router as paper_router
from app.controllers.note_route import router as note_router
from app.controllers.search_route import router as search_router
from app.controllers.collection_routes import router as collection_router
from app.controllers.analytics_route import router as analytics_router
from app.controllers.permission_routes import router as permission_router


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
app.include_router(note_router)
app.include_router(search_router)
app.include_router(collection_router)
app.include_router(analytics_router)
app.include_router(permission_router)

@app.get("/")
async def root():
    return {"message": "Welcome to inquiro server!"}