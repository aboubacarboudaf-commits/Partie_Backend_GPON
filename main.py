import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import CORS_ORIGINS
from core.scheduler import boucle_synchronisation_zabbix
from routes import (
    audit_logs,
    auth,
    centraux,
    equipements,
    incidents,
    liaisons,
    maintenances,
    rapports,
    reseaux,
    statistics,
    type_equipements,
    type_liaisons,
    upload,
    utilisateurs,
    zabbix,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    tache_zabbix = asyncio.create_task(boucle_synchronisation_zabbix())
    yield
    tache_zabbix.cancel()


app = FastAPI(title="GPONMap API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(utilisateurs.router, prefix=API_PREFIX)
app.include_router(reseaux.router, prefix=API_PREFIX)
app.include_router(centraux.router, prefix=API_PREFIX)
app.include_router(type_equipements.router, prefix=API_PREFIX)
app.include_router(type_liaisons.router, prefix=API_PREFIX)
app.include_router(equipements.router, prefix=API_PREFIX)
app.include_router(liaisons.router, prefix=API_PREFIX)
app.include_router(incidents.router, prefix=API_PREFIX)
app.include_router(maintenances.router, prefix=API_PREFIX)
app.include_router(rapports.router, prefix=API_PREFIX)
app.include_router(statistics.router, prefix=API_PREFIX)
app.include_router(zabbix.router, prefix=API_PREFIX)
app.include_router(audit_logs.router, prefix=API_PREFIX)
app.include_router(upload.router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"message": "API GPONMap OK"}
