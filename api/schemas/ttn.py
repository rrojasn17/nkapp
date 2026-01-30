from pydantic import BaseModel, Field
from typing import Any, Dict

class TTNWebhookIn(BaseModel):
    raw: Dict[str, Any] = Field(default_factory=dict)
