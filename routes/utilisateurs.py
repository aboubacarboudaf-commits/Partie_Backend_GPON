from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from core.audit import log_action
from core.security import get_current_user, hash_password, require_admin, verify_password
from core.uploads import sauvegarder_image
from database import get_db
from models import Utilisateur
from schemas.auth import ChangerMotDePasseRequest
from schemas.utilisateur import UtilisateurCreate, UtilisateurUpdate

router = APIRouter(prefix="/utilisateurs", tags=["utilisateurs"])


def _out(u: Utilisateur) -> dict:
    return {
        "id": u.id,
        "matricule": u.matricule,
        "nom": u.nom,
        "email": u.email,
        "role": u.role,
        "role_libelle": u.role_libelle,
        "est_actif": u.est_actif,
        "photo_url": u.photo_url,
    }


def _lister(db: Session):
    items = db.query(Utilisateur).filter(Utilisateur.supprime == False).all()  # noqa: E712
    return [_out(u) for u in items]


@router.get("")
@router.get("/")
def lister(db: Session = Depends(get_db), _=Depends(require_admin)):
    return _lister(db)


def _creer(payload: UtilisateurCreate, request: Request, db: Session, utilisateur: Utilisateur):
    existant = db.query(Utilisateur).filter(Utilisateur.email == payload.email).first()
    if existant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cet email est déjà utilisé")

    nouvel_utilisateur = Utilisateur(
        nom=payload.nom,
        email=payload.email,
        matricule=payload.matricule,
        mot_de_passe_hash=hash_password(payload.mot_de_passe),
        role=payload.role or 2,
    )
    db.add(nouvel_utilisateur)
    db.commit()
    db.refresh(nouvel_utilisateur)
    log_action(
        db, "creation", "utilisateur", nouvel_utilisateur.id,
        f"Création utilisateur: {nouvel_utilisateur.nom} ({nouvel_utilisateur.email}) par admin {utilisateur.nom}",
        utilisateur, request,
    )
    return _out(nouvel_utilisateur)


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
def creer(
    payload: UtilisateurCreate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    return _creer(payload, request, db, utilisateur)


@router.put("/moi/changer-mot-de-passe")
def changer_mon_mot_de_passe(
    payload: ChangerMotDePasseRequest,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(get_current_user),
):
    if not verify_password(payload.ancien_mot_de_passe, utilisateur.mot_de_passe_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ancien mot de passe incorrect")
    if payload.nouveau_mot_de_passe != payload.confirmation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Les mots de passe ne correspondent pas")

    utilisateur.mot_de_passe_hash = hash_password(payload.nouveau_mot_de_passe)
    db.commit()
    return {"message": "Mot de passe modifié avec succès"}


@router.post("/moi/photo")
async def changer_ma_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(get_current_user),
):
    url = await sauvegarder_image(file, "photos")
    utilisateur.photo_url = url
    db.commit()
    return {"photo_url": url}


@router.put("/{utilisateur_id}")
def modifier(
    utilisateur_id: int,
    payload: UtilisateurUpdate,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    cible = db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id, Utilisateur.supprime == False).first()  # noqa: E712
    if not cible:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cible, field, value)
    db.commit()
    db.refresh(cible)
    log_action(db, "modification", "utilisateur", cible.id, f"Modification utilisateur: {cible.nom}", utilisateur, request)
    return _out(cible)


@router.put("/{utilisateur_id}/activer")
def activer(
    utilisateur_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    cible = db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id, Utilisateur.supprime == False).first()  # noqa: E712
    if not cible:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    cible.est_actif = True
    db.commit()
    db.refresh(cible)
    log_action(db, "modification", "utilisateur", cible.id, f"Activation utilisateur: {cible.nom}", utilisateur, request)
    return _out(cible)


@router.put("/{utilisateur_id}/desactiver")
def desactiver(
    utilisateur_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    cible = db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id, Utilisateur.supprime == False).first()  # noqa: E712
    if not cible:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    cible.est_actif = False
    db.commit()
    db.refresh(cible)
    log_action(db, "modification", "utilisateur", cible.id, f"Désactivation utilisateur: {cible.nom}", utilisateur, request)
    return _out(cible)


@router.delete("/{utilisateur_id}")
def supprimer(
    utilisateur_id: int,
    request: Request,
    db: Session = Depends(get_db),
    utilisateur: Utilisateur = Depends(require_admin),
):
    cible = db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id, Utilisateur.supprime == False).first()  # noqa: E712
    if not cible:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    nom = cible.nom
    db.delete(cible)
    db.commit()
    log_action(db, "suppression", "utilisateur", utilisateur_id, f"Suppression utilisateur: {nom} par admin {utilisateur.nom}", utilisateur, request)
    return {"message": "Utilisateur supprimé"}
