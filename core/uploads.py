import os
import uuid

from fastapi import HTTPException, UploadFile, status

UPLOADS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
EXTENSIONS_AUTORISEES = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp"}


async def sauvegarder_image(file: UploadFile, sous_dossier: str) -> str:
    """Enregistre une image uploadée dans uploads/<sous_dossier>/ et retourne son URL publique."""
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in EXTENSIONS_AUTORISEES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format de fichier non autorisé")

    dossier = os.path.join(UPLOADS_ROOT, sous_dossier)
    os.makedirs(dossier, exist_ok=True)

    nom_fichier = f"{uuid.uuid4().hex}{extension}"
    chemin = os.path.join(dossier, nom_fichier)
    contenu = await file.read()
    with open(chemin, "wb") as f:
        f.write(contenu)

    return f"/uploads/{sous_dossier}/{nom_fichier}"
