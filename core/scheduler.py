import asyncio
import os

from database import SessionLocal
from routes.zabbix import synchroniser_zabbix

INTERVALLE_SECONDES = int(os.getenv("ZABBIX_REFRESH_INTERVAL", "60"))


async def boucle_synchronisation_zabbix() -> None:
    """Interroge Zabbix en tâche de fond, indépendamment de toute page ouverte dans un
    navigateur, pour que les pannes/rétablissements détectés côté Zabbix se répercutent
    automatiquement dans l'application (création/fermeture d'incidents) sans action
    manuelle ni frontend ouvert."""
    while True:
        try:
            db = SessionLocal()
            try:
                await asyncio.to_thread(synchroniser_zabbix, db)
            finally:
                db.close()
        except Exception as exc:  # ne jamais arrêter la boucle sur une erreur ponctuelle
            print(f"[zabbix-scheduler] synchronisation automatique échouée: {exc}")
        await asyncio.sleep(INTERVALLE_SECONDES)
