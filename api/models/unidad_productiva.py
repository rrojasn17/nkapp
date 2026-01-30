from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class UnidadProductiva(Base):
    __tablename__ = "unidades_productivas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True, nullable=False)

    nombre = Column(String, nullable=False)
    area = Column(Float, nullable=True)
    descripcion = Column(String, nullable=True)
    cualidades = Column(String, nullable=True)
    tipo = Column(String, nullable=True)
    categoria = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    georreferenciacion = Column(String, nullable=True)

    usuario = relationship("Usuario", back_populates="unidades_productivas")
    dispositivos = relationship("Dispositivo", back_populates="unidad_productiva", cascade="all, delete-orphan")
