from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker

from models import Base

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "clientes.db"
engine = create_engine(
    f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False}
)


@event.listens_for(engine, "connect")
def _ativar_chaves_estrangeiras(dbapi_conn, _record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False))


def init_db() -> None:
    Base.metadata.create_all(engine)
