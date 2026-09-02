from typing import Optional

from pydantic import BaseModel


class ReseauCreate(BaseModel):
    nom: str
    description: Optional[str] = None
