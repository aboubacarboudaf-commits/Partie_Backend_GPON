from sqlalchemy import Column, Integer, String, SmallInteger, Boolean, TIMESTAMP, func

from database import Base


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True)
    matricule = Column(String(20), unique=True, nullable=True)
    nom = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    mot_de_passe_hash = Column(String(255), nullable=False)
    role = Column(SmallInteger, nullable=False, default=3)
    est_actif = Column(Boolean, default=True)
    email_verifie = Column(Boolean, default=False)
    jeton_reinitialisation = Column(String(255), nullable=True)
    expiration_jeton = Column(TIMESTAMP, nullable=True)
    derniere_connexion = Column(TIMESTAMP, nullable=True)
    date_creation = Column(TIMESTAMP, server_default=func.now())
    date_modification = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    supprime = Column(Boolean, default=False)
    photo_url = Column(String(255), nullable=True)

    ROLE_LIBELLES = {1: "Administrateur", 2: "Technicien", 3: "Client"}

    @property
    def role_libelle(self):
        return self.ROLE_LIBELLES.get(self.role, "Inconnu")
