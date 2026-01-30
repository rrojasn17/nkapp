from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Dispositivo(Base):
    __tablename__ = "dispositivos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True, nullable=False)
    unidad_productiva_id = Column(Integer, ForeignKey("unidades_productivas.id"), index=True, nullable=False)

    marca = Column(String, nullable=True)
    identificador_dispositivo = Column(String, nullable=True)
    tipo = Column(String, nullable=True)

    eui = Column(String, unique=True, index=True, nullable=False)

    usuario = relationship("Usuario", back_populates="dispositivos")
    unidad_productiva = relationship("UnidadProductiva", back_populates="dispositivos")
    datos = relationship("Dato",back_populates="dispositivo",cascade="all, delete-orphan")

