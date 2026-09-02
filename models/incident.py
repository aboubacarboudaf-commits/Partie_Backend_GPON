from sqlalchemy import Column, Integer, String, Text, Date, Boolean, Enum, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship

from database import Base

INCIDENT_SOURCES = ("manuel", "automatique")
INCIDENT_STATUTS = ("ouvert", "en_cours", "resolu", "ferme")
INCIDENT_PRIORITES = ("basse", "moyenne", "haute", "critique")


class Incident(Base):
    __tablename__ = "incidents"

    id_incident = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    source = Column(Enum(*INCIDENT_SOURCES), default="manuel")
    description = Column(Text, nullable=False)
    equipement_id = Column(Integer, ForeignKey("equipements.id_equipement", ondelete="SET NULL"), nullable=True)
    liaison_id = Column(Integer, ForeignKey("liaisons.id", ondelete="SET NULL"), nullable=True)
    statut = Column(Enum(*INCIDENT_STATUTS), default="ouvert")
    priorite = Column(Enum(*INCIDENT_PRIORITES), default="moyenne")
    date_ouverture = Column(Date, nullable=False)
    date_fermeture = Column(Date, nullable=True)
    supprime = Column(Boolean, default=False)
    date_creation = Column(TIMESTAMP, server_default=func.now())
    date_modification = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    zabbix_eventid = Column(String(50), nullable=True)

    equipement = relationship("Equipement")
