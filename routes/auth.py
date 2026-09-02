import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from core.audit import log_action
from core.security import create_access_token, hash_password, verify_password
from database import get_db
from models import Utilisateur
from schemas.auth import (
    ChangerMotDePasseRequest,
    ConnexionRequest,
    MotDePasseOublieRequest,
    ReinitialiserMotDePasseRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _utilisateur_public(utilisateur: Utilisateur) -> dict:
    return {
        "id": utilisateur.id,
        "matricule": utilisateur.matricule,
        "nom": utilisateur.nom,
        "email": utilisateur.email,
        "role": utilisateur.role,
        "role_libelle": utilisateur.role_libelle,
        "est_actif": utilisateur.est_actif,
        "photo_url": utilisateur.photo_url,
    }


@router.post("/connexion")
def connexion(payload: ConnexionRequest, request: Request, db: Session = Depends(get_db)):
    utilisateur = (
        db.query(Utilisateur)
        .filter(
            (Utilisateur.email == payload.identifiant) | (Utilisateur.matricule == payload.identifiant),
            Utilisateur.supprime == False,  # noqa: E712
        )
        .first()
    )

    if not utilisateur or not verify_password(payload.mot_de_passe, utilisateur.mot_de_passe_hash):
        if utilisateur:
            log_action(
                db,
                action="connexion",
                entite="utilisateur",
                entite_id=utilisateur.id,
                description=f"Échec connexion: {utilisateur.nom} - Mot de passe incorrect",
                request=request,
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiant ou mot de passe incorrect")

    if not utilisateur.est_actif:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")

    utilisateur.derniere_connexion = datetime.now(timezone.utc)
    db.commit()
    db.refresh(utilisateur)

    log_action(
        db,
        action="connexion",
        entite="utilisateur",
        entite_id=utilisateur.id,
        description=f"Connexion réussie: {utilisateur.nom} ({utilisateur.email})",
        utilisateur=utilisateur,
        request=request,
    )

    token = create_access_token(utilisateur)
    return {
        "tokens": {"access_token": token},
        "utilisateur": _utilisateur_public(utilisateur),
    }


@router.post("/mot-de-passe-oublie")
def mot_de_passe_oublie(payload: MotDePasseOublieRequest, db: Session = Depends(get_db)):
    utilisateur = db.query(Utilisateur).filter(
        Utilisateur.email == payload.email, Utilisateur.supprime == False  # noqa: E712
    ).first()

    if utilisateur:
        token = secrets.token_urlsafe(32)
        utilisateur.jeton_reinitialisation = token
        utilisateur.expiration_jeton = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        # Pas de serveur SMTP configuré pour l'instant : le lien est journalisé côté serveur
        # pour permettre le test manuel du flux de réinitialisation.
        print(f"[reset-password] lien pour {utilisateur.email}: /reinitialiser-mot-de-passe?token={token}")

    # Réponse identique que l'email existe ou non, pour ne pas divulguer les comptes existants.
    return {"message": "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé."}


@router.post("/reinitialiser-mot-de-passe")
def reinitialiser_mot_de_passe(payload: ReinitialiserMotDePasseRequest, db: Session = Depends(get_db)):
    if payload.nouveau_mot_de_passe != payload.confirmation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Les mots de passe ne correspondent pas")

    utilisateur = db.query(Utilisateur).filter(
        Utilisateur.jeton_reinitialisation == payload.token,
        Utilisateur.supprime == False,  # noqa: E712
    ).first()

    if not utilisateur or not utilisateur.expiration_jeton:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien de réinitialisation invalide")

    expiration = utilisateur.expiration_jeton
    if expiration.tzinfo is None:
        expiration = expiration.replace(tzinfo=timezone.utc)
    if expiration < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien de réinitialisation expiré")

    utilisateur.mot_de_passe_hash = hash_password(payload.nouveau_mot_de_passe)
    utilisateur.jeton_reinitialisation = None
    utilisateur.expiration_jeton = None
    db.commit()

    return {"message": "Mot de passe réinitialisé avec succès"}
