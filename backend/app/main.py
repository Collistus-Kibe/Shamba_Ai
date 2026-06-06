import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database.session import engine, Base, SessionLocal
from app.services.market_service import MarketService

# Import routers
from app.api import auth, farms, assistant, diseases, weather, market, notifications

# Create database tables (SQLite / PostgreSQL / TiDB compatible)
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")
except Exception as e:
    print(f"Error initializing database tables: {e}")

# Seed market price details on startup
try:
    db = SessionLocal()
    MarketService.seed_prices_if_empty(db)
    db.close()
except Exception as e:
    print(f"Failed to seed initial database logs: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Shamba AI backend API - agricultural intelligence platform serving crop diagnostics, sensor logs, and market pricing.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS configuration
origins = [
    "http://localhost:5173",  # Vite default port
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "*"  # Allows connection from any hosted staging/production domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mapping (for serving plant disease image uploads)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(os.path.join(STATIC_DIR, "uploads"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Mount API Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(farms.router, prefix=f"{settings.API_V1_STR}/farms", tags=["Farms"])
app.include_router(assistant.router, prefix=f"{settings.API_V1_STR}/assistant", tags=["AI Assistant"])
app.include_router(diseases.router, prefix=f"{settings.API_V1_STR}/diseases", tags=["Disease Detection"])
app.include_router(weather.router, prefix=f"{settings.API_V1_STR}/weather", tags=["Environmental Intelligence"])
app.include_router(market.router, prefix=f"{settings.API_V1_STR}/market", tags=["Market Intelligence"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["Notifications"])

# Serve frontend built files if present, otherwise default to welcome JSON
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {
            "status": "online",
            "message": "Welcome to Shamba AI Core API. Access the Interactive API documentation at /docs. Frontend not built."
        }
