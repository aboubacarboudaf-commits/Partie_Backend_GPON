from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, Enum, func

from database import Base

TYPE_EQUIPEMENT_CATEGORIES = ("actif", "passif", "cable", "autre")
ICONE_TYPES = ("antd", "upload")


class TypeEquipement(Base):
    __tablename__ = "type_equipement"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(100), nullable=False, unique=True)
    categorie = Column(Enum(*TYPE_EQUIPEMENT_CATEGORIES), nullable=False, default="actif")
    description = Column(Text, nullable=True)
    date_creation = Column(TIMESTAMP, server_default=func.now())
    date_modification = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    supprime = Column(Boolean, default=False)
    est_actif = Column(Boolean, default=True)
    icone = Column(String(50), default="AppstoreOutlined", nullable=True)
    icone_url = Column(String(255), nullable=True)
    icone_type = Column(Enum(*ICONE_TYPES), default="antd")
    possede_ip = Column(Boolean, nullable=False, default=True)
    possede_port = Column(Boolean, nullable=False, default=False)
    possede_ratio = Column(Boolean, nullable=False, default=False)
    prefixe_port = Column(String(20), default="Port", nullable=True)
