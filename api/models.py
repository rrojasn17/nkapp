from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text,
    func,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, DOUBLE_PRECISION
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    correo: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)

    hash_contrasena: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(50), nullable=False, default="usuario")

    # token simple para autenticación
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    token_restablecer_contrasena: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    unidades_productivas: Mapped[List["UnidadProductiva"]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    dispositivos: Mapped[List["Dispositivo"]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
    )


class UnidadProductiva(Base):
    __tablename__ = "unidades_productivas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    cualidades: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    categoria: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    direccion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    georreferenciacion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    usuario: Mapped["Usuario"] = relationship(back_populates="unidades_productivas")
    dispositivos: Mapped[List["Dispositivo"]] = relationship(
        back_populates="unidad_productiva",
        cascade="all, delete-orphan",
    )


class Dispositivo(Base):
    __tablename__ = "dispositivos"
    __table_args__ = (
        UniqueConstraint("eui", name="uq_dispositivos_eui"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unidad_productiva_id: Mapped[int] = mapped_column(
        ForeignKey("unidades_productivas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    marca: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    identificador_dispositivo: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    tipo: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    eui: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    usuario: Mapped["Usuario"] = relationship(back_populates="dispositivos")
    unidad_productiva: Mapped["UnidadProductiva"] = relationship(back_populates="dispositivos")

    # modelo nuevo
    mediciones: Mapped[List["Medicion"]] = relationship(
        back_populates="dispositivo",
        cascade="all, delete-orphan",
    )

    # modelo legado
    datos_legado: Mapped[List["DatoSensor"]] = relationship(
        back_populates="dispositivo",
        cascade="all, delete-orphan",
    )


class DatoSensor(Base):
    __tablename__ = "datos_sensor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    dispositivo_id: Mapped[int] = mapped_column(
        ForeignKey("dispositivos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    variable: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    valor: Mapped[float] = mapped_column(Float, nullable=False)

    eui: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    dispositivo: Mapped["Dispositivo"] = relationship(back_populates="datos_legado")


class Medicion(Base):
    __tablename__ = "mediciones"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    dispositivo_id: Mapped[int] = mapped_column(
        ForeignKey("dispositivos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # 'normalized' | 'decoded'
    origen: Mapped[str] = mapped_column(String(20), nullable=False, default="decoded")

    json_crudo: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    json_decodificado: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    json_normalizado: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    dispositivo: Mapped["Dispositivo"] = relationship(back_populates="mediciones")
    valores: Mapped[List["ValorMedicion"]] = relationship(
        back_populates="medicion",
        cascade="all, delete-orphan",
    )


class ValorMedicion(Base):
    __tablename__ = "valores_medicion"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    medicion_id: Mapped[int] = mapped_column(
        ForeignKey("mediciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nombre_variable: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    ruta_variable: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    unidad: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    valor: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    medicion: Mapped["Medicion"] = relationship(back_populates="valores")
