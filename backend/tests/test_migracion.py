import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from prosta_ai.db import Base
import prosta_ai.models  # noqa: F401


def _columnas(engine):
    insp = sa.inspect(engine)
    return {t: sorted(c["name"] for c in insp.get_columns(t)) for t in insp.get_table_names()
            if t != "alembic_version"}


def test_migracion_equivale_a_modelos(tmp_path):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    migrada = sa.create_engine(url)
    modelos = sa.create_engine(f"sqlite:///{tmp_path / 'o.db'}")
    Base.metadata.create_all(modelos)
    assert _columnas(migrada) == _columnas(modelos)
    assert set(_columnas(migrada)) == {
        "usuario", "estudio", "archivo", "modelo", "trabajo", "etapa_trabajo", "resultado"}
    indices = {i["name"] for t in ("trabajo", "estudio") for i in sa.inspect(migrada).get_indexes(t)}
    assert {"ix_trabajo_estado", "ix_estudio_id_usuario"} <= indices
    command.downgrade(cfg, "base")
