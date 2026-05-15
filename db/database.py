from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base

# Используем SQLite для простоты
DATABASE_URL = "sqlite:///./job_search.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Создаёт таблицы и добавляет базовые категории."""
    Base.metadata.create_all(bind=engine)
    # Добавим несколько категорий, если их нет
    with SessionLocal() as session:
        from .models import Category
        if session.query(Category).count() == 0:
            categories = ["IT", "Маркетинг", "Продажи", "Дизайн", "Управление"]
            for cat in categories:
                session.add(Category(name=cat))
            session.commit()


def get_db() -> Session:
    """Возвращает сессию БД (используется в хендлерах)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()