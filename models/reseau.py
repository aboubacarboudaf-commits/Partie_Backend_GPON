from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, func

from database import Base


class Reseau(Base):
    __tablename__ = "reseaux"

    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    date_creation = Column(TIMESTAMP, server_default=func.now())
    supprime = Column(Boolean, default=False)
