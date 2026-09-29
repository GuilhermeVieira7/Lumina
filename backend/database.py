# ==========================================
# DATABASE - Configuração SQLAlchemy
# Sistema de Apoio Educacional para TEA
# ==========================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tea_system.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_columns():
    """Adicionar colunas novas em tabelas já existentes.

    create_all() cria tabelas, mas não altera as que já existem; sem isto,
    bancos locais criados por versões anteriores quebrariam ao atualizar.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            present = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in present:
                    continue
                col_type = column.type.compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN {column.name} {col_type}'))
                default = column.default.arg if column.default is not None and column.default.is_scalar else None
                if default is not None:
                    conn.execute(
                        text(f'UPDATE {table.name} SET {column.name} = :value WHERE {column.name} IS NULL'),
                        {"value": default},
                    )


def get_db():
    """Dependency para injetar sessão do banco em cada request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
