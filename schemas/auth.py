from pydantic import BaseModel


class ConnexionRequest(BaseModel):
    identifiant: str
    mot_de_passe: str


class MotDePasseOublieRequest(BaseModel):
    email: str


class ReinitialiserMotDePasseRequest(BaseModel):
    token: str
    nouveau_mot_de_passe: str
    confirmation: str


class ChangerMotDePasseRequest(BaseModel):
    ancien_mot_de_passe: str
    nouveau_mot_de_passe: str
    confirmation: str
