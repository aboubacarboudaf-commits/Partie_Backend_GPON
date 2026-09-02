from sqlalchemy import Column, Integer, String, Text, Date, Boolean, Enum, TIMESTAMP, func

from database import Base

RAPPORT_FORMATS = ("pdf", "excel", "csv")


class Rapport(Base):
    __tablename__ = "rapports"

    id_rapport = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    titre = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    date_rapport = Column(Date, nullable=False)
    format = Column(Enum(*RAPPORT_FORMATS), default="pdf")
    contenu = Column(Text, nullable=True)
    supprime = Column(Boolean, default=False)
    date_creation = Column(TIMESTAMP, server_default=func.now())
    date_modification = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
