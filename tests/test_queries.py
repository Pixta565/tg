import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, User, Category, Resume, Vacancy, Response
from db.queries import *

# Фикстура: in-memory БД
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Добавляем тестовые категории
    cats = ["IT", "Маркетинг"]
    for name in cats:
        session.add(Category(name=name))
    session.commit()
    yield session
    session.close()

def test_create_and_get_user(db_session):
    user = create_user(db_session, 12345, "testuser", "Test", "job_seeker")
    assert user.id is not None
    fetched = get_user_by_telegram_id(db_session, 12345)
    assert fetched is not None
    assert fetched.role == "job_seeker"

def test_create_resume_and_filter(db_session):
    user = create_user(db_session, 111, "alice", "Alice", "job_seeker")
    cat = db_session.query(Category).filter(Category.name == "IT").first()
    resume = create_resume(db_session, user.id, "Python Dev", "desc", "python", "2 years", 100000, cat.id)
    resumes = get_active_resumes(db_session)
    assert len(resumes) == 1
    assert resumes[0].title == "Python Dev"

def test_response_workflow(db_session):
    employer = create_user(db_session, 222, "boss", "Boss", "employer")
    seeker = create_user(db_session, 333, "worker", "Worker", "job_seeker")
    cat = db_session.query(Category).first()
    vacancy = create_vacancy(db_session, employer.id, "Java Dev", "desc", "java", 120000, "Moscow", cat.id)
    resume = create_resume(db_session, seeker.id, "Java Exp", "desc", "java", "3 years", 110000, cat.id)
    response = create_response(db_session, resume.id, vacancy.id)
    assert response.status == "pending"
    updated = update_response_status(db_session, response.id, "accepted")
    assert updated.status == "accepted"
    responses_for_vac = get_responses_for_vacancy(db_session, vacancy.id)
    assert len(responses_for_vac) == 1
    assert responses_for_vac[0].status == "accepted"