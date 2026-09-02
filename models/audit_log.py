from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship

from database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id_auditlog = Column(Integer, primary_key=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    entite = Column(String(50), nullable=True)
    entite_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    ip_adresse = Column(String(45), nullable=True)
    date_action = Column(TIMESTAMP, server_default=func.now())

    utilisateur = relationship("Utilisateur")
