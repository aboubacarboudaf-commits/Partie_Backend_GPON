from sqlalchemy import Column, Integer, String, Text, SmallInteger, Boolean, DateTime, func

from database import Base


class TypeLiaison(Base):
    __tablename__ = "type_liaison"

    id = Column(Integer, primary_key=True)
    libelle = Column(String(50), nullable=False, unique=True)
    couleur = Column(String(7), nullable=False, default="#1890ff")
    style_trait = Column(String(20), nullable=False, default="solide")
    epaisseur = Column(SmallInteger, nullable=False, default=2)
    description = Column(Text, nullable=True)
    supprime = Column(Boolean, nullable=False, default=False)
    date_creation = Column(DateTime, nullable=False, server_default=func.now())
