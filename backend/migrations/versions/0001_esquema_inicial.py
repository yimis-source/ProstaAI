"""Esquema inicial: usuario, estudio, archivo, modelo, trabajo, etapa_trabajo, resultado

Revision ID: 0001
Revises:
Create Date: 2026-11-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

ESTADOS = "('pendiente', 'en proceso', 'completado', 'fallido')"
ETAPAS = "('control de calidad', 'preparación', 'segmentación', 'ROI', 'evaluación')"


def _fecha(nombre: str, **kw) -> sa.Column:
    return sa.Column(nombre, sa.DateTime(timezone=True), **kw)


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id_usuario", sa.Integer, sa.Identity(), primary_key=True),
        sa.Column("alias", sa.String(30), nullable=False),
        sa.Column("hash_contrasena", sa.String(255), nullable=False),
        _fecha("fecha_creacion", nullable=False),
        sa.UniqueConstraint("alias"),
    )
    op.create_table(
        "estudio",
        sa.Column("id_estudio", sa.Integer, sa.Identity(), primary_key=True),
        sa.Column("codigo_anonimo", sa.String(12), nullable=False),
        sa.Column("id_usuario", sa.Integer, sa.ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False),
        sa.Column("formato", sa.String(5), nullable=False),
        _fecha("fecha_carga", nullable=False),
        sa.Column("estado_admision", sa.String(15), nullable=False),
        sa.UniqueConstraint("codigo_anonimo"),
        sa.CheckConstraint("formato IN ('DICOM', 'NIfTI')", name="ck_estudio_formato"),
        sa.CheckConstraint("estado_admision IN ('admitido', 'no compatible')", name="ck_estudio_estado_admision"),
    )
    op.create_index("ix_estudio_id_usuario", "estudio", ["id_usuario"])
    op.create_table(
        "archivo",
        sa.Column("id_archivo", sa.Integer, sa.Identity(), primary_key=True),
        sa.Column("id_estudio", sa.Integer, sa.ForeignKey("estudio.id_estudio", ondelete="CASCADE"), nullable=False),
        sa.Column("ruta", sa.String(255), nullable=False),
        sa.Column("tamano_bytes", sa.BigInteger, nullable=False),
        sa.Column("hash_sha256", sa.CHAR(64), nullable=False),
        sa.Column("valido", sa.Boolean, nullable=False),
    )
    op.create_table(
        "modelo",
        sa.Column("id_modelo", sa.Integer, sa.Identity(), primary_key=True),
        sa.Column("nombre", sa.String(50), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("ruta_pesos", sa.String(255)),
        sa.Column("hash_pesos", sa.CHAR(64)),
        sa.Column("ruta_configuracion", sa.String(255)),
        _fecha("fecha_registro", nullable=False),
        sa.UniqueConstraint("nombre", "version", name="uq_modelo_nombre_version"),
    )
    op.create_table(
        "trabajo",
        sa.Column("id_trabajo", sa.Integer, sa.Identity(), primary_key=True),
        sa.Column("id_estudio", sa.Integer, sa.ForeignKey("estudio.id_estudio", ondelete="CASCADE"), nullable=False),
        sa.Column("id_modelo", sa.Integer, sa.ForeignKey("modelo.id_modelo"), nullable=False),
        sa.Column("estado", sa.String(12), nullable=False),
        _fecha("fecha_creacion", nullable=False),
        _fecha("fecha_inicio"),
        _fecha("fecha_fin"),
        sa.Column("etapa_fallida", sa.String(25)),
        sa.Column("mensaje_error", sa.Text),
        sa.CheckConstraint(f"estado IN {ESTADOS}", name="ck_trabajo_estado"),
    )
    op.create_index("ix_trabajo_estado", "trabajo", ["estado"])
    op.create_table(
        "etapa_trabajo",
        sa.Column("id_etapa", sa.Integer, sa.Identity(), primary_key=True),
        sa.Column("id_trabajo", sa.Integer, sa.ForeignKey("trabajo.id_trabajo", ondelete="CASCADE"), nullable=False),
        sa.Column("nombre", sa.String(25), nullable=False),
        sa.Column("estado", sa.String(12), nullable=False),
        _fecha("fecha_inicio"),
        _fecha("fecha_fin"),
        sa.Column("duracion_s", sa.Numeric(7, 2)),
        sa.CheckConstraint(f"nombre IN {ETAPAS}", name="ck_etapa_nombre"),
        sa.CheckConstraint(f"estado IN {ESTADOS}", name="ck_etapa_estado"),
    )
    op.create_table(
        "resultado",
        sa.Column("id_resultado", sa.Integer, sa.Identity(), primary_key=True),
        sa.Column("id_trabajo", sa.Integer, sa.ForeignKey("trabajo.id_trabajo", ondelete="CASCADE"), nullable=False),
        sa.Column("ruta_mascara", sa.String(255), nullable=False),
        sa.Column("dice", sa.Numeric(4, 3)),
        sa.Column("iou", sa.Numeric(4, 3)),
        sa.Column("tiempo_total_s", sa.Numeric(7, 2)),
        _fecha("fecha_registro", nullable=False),
        sa.UniqueConstraint("id_trabajo"),
        sa.CheckConstraint("dice IS NULL OR (dice >= 0 AND dice <= 1)", name="ck_resultado_dice"),
        sa.CheckConstraint("iou IS NULL OR (iou >= 0 AND iou <= 1)", name="ck_resultado_iou"),
    )


def downgrade() -> None:
    for tabla in ("resultado", "etapa_trabajo", "trabajo", "modelo", "archivo", "estudio", "usuario"):
        op.drop_table(tabla)
