from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.profiles import router as profiles_router
from app.routers.chats import router as chats_router
from app.routers.posts import router as posts_router

app = FastAPI()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles_router)
app.include_router(chats_router)
app.include_router(posts_router)
