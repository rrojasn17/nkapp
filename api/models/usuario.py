from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, index=True, nullable=False)

    hash_contrasena = Column(String, nullable=False)
    rol = Column(String, nullable=False, default="usuario")

    token = Column(String, unique=True, index=True, nullable=False)
    token_restablecer_contrasena = Column(String, nullable=True)

    unidades_productivas = relationship("UnidadProductiva", back_populates="usuario", cascade="all, delete-orphan")
    dispositivos = relationship("Dispositivo", back_populates="usuario", cascade="all, delete-orphan")
