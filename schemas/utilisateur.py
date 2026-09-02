from typing import Optional

from pydantic import BaseModel, EmailStr


class UtilisateurCreate(BaseModel):
    nom: str
    email: EmailStr
    matricule: Optional[str] = None
    mot_de_passe: str
    role: Optional[int] = 2


class UtilisateurUpdate(BaseModel):
    nom: Optional[str] = None
    email: Optional[EmailStr] = None
    matricule: Optional[str] = None
    role: Optional[int] = None
