from typing import List, Optional
from sqlalchemy.orm import Session
from .models import User, Resume, Vacancy, Response, Category


# ---- Пользователи ----
def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
    return db.query(User).filter(User.telegram_id == telegram_id).first()


def create_user(db: Session, telegram_id: int, username: str, first_name: str, role: str) -> User:
    user = User(telegram_id=telegram_id, username=username, first_name=first_name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---- Резюме ----
def create_resume(db: Session, user_id: int, title: str, description: str, skills: str,
                  experience: str, desired_salary: float, category_id: int) -> Resume:
    resume = Resume(user_id=user_id, title=title, description=description, skills=skills,
                    experience=experience, desired_salary=desired_salary, category_id=category_id)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def get_resumes_by_user(db: Session, user_id: int) -> List[Resume]:
    return db.query(Resume).filter(Resume.user_id == user_id).all()


def get_active_resumes(db: Session) -> List[Resume]:
    return db.query(Resume).filter(Resume.is_active == True).all()


# ---- Вакансии ----
def create_vacancy(db: Session, user_id: int, title: str, description: str, requirements: str,
                   salary: float, location: str, category_id: int) -> Vacancy:
    vacancy = Vacancy(user_id=user_id, title=title, description=description, requirements=requirements,
                      salary=salary, location=location, category_id=category_id)
    db.add(vacancy)
    db.commit()
    db.refresh(vacancy)
    return vacancy


def get_vacancies_by_user(db: Session, user_id: int) -> List[Vacancy]:
    return db.query(Vacancy).filter(Vacancy.user_id == user_id).all()


def get_active_vacancies(db: Session) -> List[Vacancy]:
    return db.query(Vacancy).filter(Vacancy.is_active == True).all()


def search_vacancies_by_title(db: Session, keyword: str) -> List[Vacancy]:
    return db.query(Vacancy).filter(Vacancy.title.contains(keyword), Vacancy.is_active == True).all()


def filter_vacancies_by_salary(db: Session, min_salary: float) -> List[Vacancy]:
    return db.query(Vacancy).filter(Vacancy.salary >= min_salary, Vacancy.is_active == True).all()


def filter_vacancies_by_category(db: Session, category_id: int) -> List[Vacancy]:
    return db.query(Vacancy).filter(Vacancy.category_id == category_id, Vacancy.is_active == True).all()


# ---- Отклики ----
def create_response(db: Session, resume_id: int, vacancy_id: int) -> Response:
    response = Response(resume_id=resume_id, vacancy_id=vacancy_id)
    db.add(response)
    db.commit()
    db.refresh(response)
    return response


def get_responses_for_vacancy(db: Session, vacancy_id: int) -> List[Response]:
    return db.query(Response).filter(Response.vacancy_id == vacancy_id).all()


def get_responses_for_resume(db: Session, resume_id: int) -> List[Response]:
    return db.query(Response).filter(Response.resume_id == resume_id).all()


def update_response_status(db: Session, response_id: int, new_status: str) -> Optional[Response]:
    response = db.query(Response).filter(Response.id == response_id).first()
    if response:
        response.status = new_status
        db.commit()
        db.refresh(response)
    return response


# ---- Категории ----
def get_all_categories(db: Session) -> List[Category]:
    return db.query(Category).all()


def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    return db.query(Category).filter(Category.name == name).first()

def filter_vacancies_by_category(db: Session, category_id: int) -> List[Vacancy]:
    return db.query(Vacancy).filter(Vacancy.category_id == category_id, Vacancy.is_active == True).all()

def delete_user_data(db: Session, user_id: int) -> None:
    # Удаляем отклики, связанные с резюме пользователя
    resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    for resume in resumes:
        db.query(Response).filter(Response.resume_id == resume.id).delete()
    # Удаляем отклики, связанные с вакансиями пользователя
    vacancies = db.query(Vacancy).filter(Vacancy.user_id == user_id).all()
    for vacancy in vacancies:
        db.query(Response).filter(Response.vacancy_id == vacancy.id).delete()
    # Удаляем резюме и вакансии
    db.query(Resume).filter(Resume.user_id == user_id).delete()
    db.query(Vacancy).filter(Vacancy.user_id == user_id).delete()
    db.commit()

def filter_resumes_by_category(db: Session, category_id: int) -> List[Resume]:
    return db.query(Resume).filter(Resume.category_id == category_id, Resume.is_active == True).all()

def delete_resume(db: Session, resume_id: int) -> None:
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if resume:
        db.delete(resume)
        db.commit()