from sqlalchemy import Column, Integer, String, Text, Float, Boolean, TIMESTAMP, ForeignKey, Enum, func
from sqlalchemy.orm import relationship

from database import Base

CENTRAL_TYPES = ("central", "sous_repartiteur", "chambre", "poteau")


class Central(Base):
    __tablename__ = "centraux"

    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=True)
    adresse = Column(Text, nullable=True)
    ville = Column(String(100), nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    type = Column(Enum(*CENTRAL_TYPES), default="central")
    supprime = Column(Boolean, default=False)
    date_creation = Column(TIMESTAMP, server_default=func.now())
    reseau_id = Column(Integer, ForeignKey("reseaux.id"), nullable=True)
    position_x = Column(Integer, default=100)
    position_y = Column(Integer, default=100)
    quartier = Column(String(100), nullable=True)

    reseau = relationship("Reseau")
