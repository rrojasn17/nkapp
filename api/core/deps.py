from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario

def get_current_user(
    db: Session = Depends(get_db),
    x_api_token: str = Header(..., alias="X-API-Token"),
) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.token == x_api_token).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido")
    return usuario
