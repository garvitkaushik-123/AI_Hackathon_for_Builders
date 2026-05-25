from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db import init_db
from routers import dashboard, costs, resources, scan, recommendations, ask, settings

app = FastAPI(title="Cloud Cost Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(costs.router)
app.include_router(resources.router)
app.include_router(scan.router)
app.include_router(recommendations.router)
app.include_router(ask.router)
app.include_router(settings.router)


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/api/health")
async def health():
    return {"status": "ok"}
