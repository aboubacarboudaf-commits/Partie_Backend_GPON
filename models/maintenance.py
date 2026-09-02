from sqlalchemy import Column, Integer, String, Text, Date, Boolean, Enum, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship

from database import Base

MAINTENANCE_TYPES = ("preventive", "corrective", "evolutive")
MAINTENANCE_STATUTS = ("planifiee", "en_cours", "terminee", "annulee")


class Maintenance(Base):
    __tablename__ = "maintenances"

    id = Column(Integer, primary_key=True)
    titre = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    equipement_id = Column(Integer, ForeignKey("equipements.id_equipement", ondelete="SET NULL"), nullable=True)
    liaison_id = Column(Integer, ForeignKey("liaisons.id", ondelete="SET NULL"), nullable=True)
    incident_id = Column(Integer, ForeignKey("incidents.id_incident", ondelete="SET NULL"), nullable=True)
    type = Column(Enum(*MAINTENANCE_TYPES), default="corrective")
    statut = Column(Enum(*MAINTENANCE_STATUTS), default="planifiee")
    date_planifiee = Column(Date, nullable=False)
    date_debut = Column(Date, nullable=True)
    date_fin = Column(Date, nullable=True)
    technicien = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    supprime = Column(Boolean, default=False)
    date_creation = Column(TIMESTAMP, server_default=func.now())
    date_modification = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    equipement = relationship("Equipement")
    incident = relationship("Incident")
