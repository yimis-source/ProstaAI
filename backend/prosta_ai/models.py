"""Tablas de la base de datos (docs/ejecucion/04_modelo_datos.md)."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger, Boolean, CHAR, CheckConstraint, DateTime, ForeignKey, Identity,
    Index, Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prosta_ai.db import Base, ahora
from prosta_ai.pipeline.stages import STAGES


def _lista(columna: str, valores) -> str:
    return f"{columna} IN (" + ", ".join(f"'{v}'" for v in valores) + ")"


ESTADOS = ("pendiente", "en proceso", "completado", "fallido")


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    alias: Mapped[str] = mapped_column(String(30), unique=True)
    hash_contrasena: Mapped[str] = mapped_column(String(255))
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    estudios: Mapped[list["Estudio"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan", passive_deletes=True
    )


class Estudio(Base):
    __tablename__ = "estudio"
    __table_args__ = (
        CheckConstraint(_lista("formato", ("DICOM", "NIfTI")), name="ck_estudio_formato"),
        CheckConstraint(
            _lista("estado_admision", ("admitido", "no compatible")),
            name="ck_estudio_estado_admision",
        ),
        Index("ix_estudio_id_usuario", "id_usuario"),
    )

    id_estudio: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    codigo_anonimo: Mapped[str] = mapped_column(String(12), unique=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario", ondelete="CASCADE"))
    formato: Mapped[str] = mapped_column(String(5))
    fecha_carga: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    estado_admision: Mapped[str] = mapped_column(String(15))

    usuario: Mapped[Usuario] = relationship(back_populates="estudios")
    archivos: Mapped[list["Archivo"]] = relationship(
        back_populates="estudio", cascade="all, delete-orphan", passive_deletes=True
    )
    trabajos: Mapped[list["Trabajo"]] = relationship(
        back_populates="estudio", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Trabajo.id_trabajo",
    )


class Archivo(Base):
    __tablename__ = "archivo"

    id_archivo: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    id_estudio: Mapped[int] = mapped_column(ForeignKey("estudio.id_estudio", ondelete="CASCADE"))
    ruta: Mapped[str] = mapped_column(String(255))
    tamano_bytes: Mapped[int] = mapped_column(BigInteger)
    hash_sha256: Mapped[str] = mapped_column(CHAR(64))
    valido: Mapped[bool] = mapped_column(Boolean, default=True)

    estudio: Mapped[Estudio] = relationship(back_populates="archivos")


class Modelo(Base):
    __tablename__ = "modelo"
    __table_args__ = (UniqueConstraint("nombre", "version", name="uq_modelo_nombre_version"),)

    id_modelo: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50))
    version: Mapped[str] = mapped_column(String(20))
    ruta_pesos: Mapped[str | None] = mapped_column(String(255))
    hash_pesos: Mapped[str | None] = mapped_column(CHAR(64))
    ruta_configuracion: Mapped[str | None] = mapped_column(String(255))
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class Trabajo(Base):
    __tablename__ = "trabajo"
    __table_args__ = (
        CheckConstraint(_lista("estado", ESTADOS), name="ck_trabajo_estado"),
        Index("ix_trabajo_estado", "estado"),
    )

    id_trabajo: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    id_estudio: Mapped[int] = mapped_column(ForeignKey("estudio.id_estudio", ondelete="CASCADE"))
    id_modelo: Mapped[int] = mapped_column(ForeignKey("modelo.id_modelo"))
    estado: Mapped[str] = mapped_column(String(12), default="pendiente")
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    etapa_fallida: Mapped[str | None] = mapped_column(String(25))
    mensaje_error: Mapped[str | None] = mapped_column(Text)

    estudio: Mapped[Estudio] = relationship(back_populates="trabajos")
    modelo: Mapped[Modelo] = relationship()
    etapas: Mapped[list["EtapaTrabajo"]] = relationship(
        back_populates="trabajo", cascade="all, delete-orphan", passive_deletes=True,
        order_by="EtapaTrabajo.id_etapa",
    )
    resultado: Mapped["Resultado | None"] = relationship(
        back_populates="trabajo", cascade="all, delete-orphan", passive_deletes=True,
        uselist=False,
    )


class EtapaTrabajo(Base):
    __tablename__ = "etapa_trabajo"
    __table_args__ = (
        CheckConstraint(_lista("nombre", STAGES), name="ck_etapa_nombre"),
        CheckConstraint(_lista("estado", ESTADOS), name="ck_etapa_estado"),
    )

    id_etapa: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    id_trabajo: Mapped[int] = mapped_column(ForeignKey("trabajo.id_trabajo", ondelete="CASCADE"))
    nombre: Mapped[str] = mapped_column(String(25))
    estado: Mapped[str] = mapped_column(String(12), default="pendiente")
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duracion_s: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))

    trabajo: Mapped[Trabajo] = relationship(back_populates="etapas")


class Resultado(Base):
    __tablename__ = "resultado"
    __table_args__ = (
        CheckConstraint("dice IS NULL OR (dice >= 0 AND dice <= 1)", name="ck_resultado_dice"),
        CheckConstraint("iou IS NULL OR (iou >= 0 AND iou <= 1)", name="ck_resultado_iou"),
    )

    id_resultado: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    id_trabajo: Mapped[int] = mapped_column(
        ForeignKey("trabajo.id_trabajo", ondelete="CASCADE"), unique=True
    )
    ruta_mascara: Mapped[str] = mapped_column(String(255))
    dice: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    iou: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    tiempo_total_s: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    trabajo: Mapped[Trabajo] = relationship(back_populates="resultado")
