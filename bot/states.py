from aiogram.fsm.state import State, StatesGroup

class CreateResume(StatesGroup):
    title = State()
    category = State()
    description = State()
    skills = State()
    experience = State()
    salary = State()

class CreateVacancy(StatesGroup):
    title = State()
    category = State()
    description = State()
    requirements = State()
    salary = State()
    location = State()

class SearchVacancies(StatesGroup):
    category = State()