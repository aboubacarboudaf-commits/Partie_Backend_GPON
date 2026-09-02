from sqlalchemy import Column, Integer, String, Date, Float, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship

from database import Base


class Equipement(Base):
    __tablename__ = "equipements"

    id_equipement = Column(Integer, primary_key=True)
    libelle = Column(String(100), nullable=False)
    etat = Column(String(30), default="actif")
    date_installation = Column(Date, nullable=True)
    version_firmware = Column(String(50), nullable=True)
    adresse_mac = Column(String(17), nullable=True)
    adresse_ip = Column(String(15), nullable=True)
    nbre_port_pon = Column(Integer, default=0)
    nbre_port = Column(Integer, default=0)
    ratio = Column(Integer, default=0)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    ville = Column(String(100), nullable=True)
    supprime = Column(Boolean, default=False)
    date_creation = Column(TIMESTAMP, server_default=func.now())
    date_modification = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    position_x = Column(Integer, default=100)
    position_y = Column(Integer, default=100)
    icone = Column(String(50), default="default", nullable=True)
    type_equipement_id = Column(Integer, ForeignKey("type_equipement.id"), nullable=False, default=1)
    central_id = Column(Integer, ForeignKey("centraux.id"), nullable=True)
    reseau_id = Column(Integer, ForeignKey("reseaux.id"), nullable=True)
    quartier = Column(String(100), nullable=True)
    zabbix_host_id = Column(String(20), nullable=True)

    type_equipement = relationship("TypeEquipement")
    central = relationship("Central")
    reseau = relationship("Reseau")
