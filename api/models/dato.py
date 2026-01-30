from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from database import Base

class Dato(Base):
    __tablename__ = "datos"

    id = Column(Integer, primary_key=True, index=True)
    dispositivo_id = Column(Integer, ForeignKey("dispositivos.id"), index=True, nullable=False)

    fecha_hora = Column(DateTime(timezone=True), nullable=False)
    origen = Column(String, nullable=False, default="none")

    json_crudo = Column(JSON, nullable=True)
    json_decodificado = Column(JSON, nullable=True)
    json_normalizado = Column(JSON, nullable=True)

    dispositivo = relationship("Dispositivo", back_populates="datos")
    valores = relationship(
        "ValorDato",
        back_populates="dato",
        cascade="all, delete-orphan"
    )


class ValorDato(Base):
    __tablename__ = "valores_dato"

    id = Column(Integer, primary_key=True, index=True)
    dato_id = Column(Integer, ForeignKey("datos.id"), index=True, nullable=False)

    nombre_variable = Column(String, nullable=False)
    ruta_variable = Column(String, nullable=True, index=True)
    unidad = Column(String, nullable=True)
    valor = Column(Float, nullable=False)

    dato = relationship("Dato", back_populates="valores")
