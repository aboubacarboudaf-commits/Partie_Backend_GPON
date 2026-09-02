from fastapi import APIRouter, Depends, UploadFile, File

from core.security import require_admin
from core.uploads import sauvegarder_image

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/icone")
async def upload_icone(file: UploadFile = File(...), _=Depends(require_admin)):
    url = await sauvegarder_image(file, "icones")
    return {"url": url}
