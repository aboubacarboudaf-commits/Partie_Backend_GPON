from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, Enum, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship

from database import Base

LIAISON_STATUTS = ("ok", "degrade", "rompu")


class Liaison(Base):
    __tablename__ = "liaisons"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("equipements.id_equipement"), nullable=False)
    destination_id = Column(Integer, ForeignKey("equipements.id_equipement"), nullable=False)
    type_liaison_id = Column(Integer, ForeignKey("type_liaison.id"), nullable=True)
    central_id = Column(Integer, ForeignKey("centraux.id"), nullable=True)
    port_source = Column(String(20), nullable=True)
    port_destination = Column(String(20), nullable=True)
    longueur_m = Column(Numeric(10, 2), nullable=True)
    date_pose = Column(Date, nullable=True)
    supprime = Column(Boolean, nullable=False, default=False)
    statut = Column(Enum(*LIAISON_STATUTS), default="ok")
    date_creation = Column(TIMESTAMP, server_default=func.now())
    date_modification = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    reseau_id = Column(Integer, ForeignKey("reseaux.id"), nullable=True)

    source = relationship("Equipement", foreign_keys=[source_id])
    destination = relationship("Equipement", foreign_keys=[destination_id])
    type_liaison = relationship("TypeLiaison")
