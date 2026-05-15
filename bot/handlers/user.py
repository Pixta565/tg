from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from db.database import get_db
from db.queries import get_user_by_telegram_id, create_user, delete_user_data
from bot.keyboards import main_menu, role_choice

router = Router()



@router.message(F.text == "❓ Помощь")
@router.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "📋 Список команд:\n\n"
        "/start - Начать работу\n"
        "/new_resume - Создать резюме (только соискатель)\n"
        "/my_resumes - Мои резюме\n"
        "/new_vacancy - Создать вакансию (только работодатель)\n"
        "/my_vacancies - Мои вакансии\n"
        "/search_candidates - Поиск соискателей (работодатель)\n"
        "/help - Помощь\n\n"
        "Также используйте кнопки меню."
    )
    await message.answer(help_text)  # убрали parse_mode

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user:
            await message.answer("Добро пожаловать! Выберите вашу роль:", reply_markup=role_choice)
            return
        await message.answer(f"С возвращением, {first_name}!", reply_markup=main_menu)

@router.message(F.text == "👤 Соискатель")
async def set_job_seeker(message: Message):
    telegram_id = message.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user:
            create_user(db, telegram_id, message.from_user.username, message.from_user.first_name, "job_seeker")
            await message.answer("Вы зарегистрированы как соискатель!", reply_markup=main_menu)
        else:
            await message.answer("Вы уже зарегистрированы. Используйте кнопку «Сменить роль» для изменения.", reply_markup=main_menu)

@router.message(F.text == "🏢 Работодатель")
async def set_employer(message: Message):
    telegram_id = message.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user:
            create_user(db, telegram_id, message.from_user.username, message.from_user.first_name, "employer")
            await message.answer("Вы зарегистрированы как работодатель!", reply_markup=main_menu)
        else:
            await message.answer("Вы уже зарегистрированы. Используйте кнопку «Сменить роль» для изменения.", reply_markup=main_menu)

@router.message(F.text == "⚙️ Сменить роль")
async def change_role(message: Message):
    await message.answer("Выберите новую роль. ВНИМАНИЕ: все ваши текущие данные (резюме/вакансии/отклики) будут удалены!", reply_markup=role_choice)

# Обработчик выбора новой роли
@router.message(F.text.in_(["👤 Соискатель", "🏢 Работодатель"]))
async def apply_new_role(message: Message):
    telegram_id = message.from_user.id
    new_role = "job_seeker" if message.text == "👤 Соискатель" else "employer"
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user:
            create_user(db, telegram_id, message.from_user.username, message.from_user.first_name, new_role)
            await message.answer(f"Вы зарегистрированы как {'соискатель' if new_role == 'job_seeker' else 'работодатель'}.", reply_markup=main_menu)
            return
        if user.role == new_role:
            await message.answer(f"Вы уже являетесь {'соискателем' if new_role == 'job_seeker' else 'работодателем'}.", reply_markup=main_menu)
            return
        # Меняем роль: удаляем связанные данные
        delete_user_data(db, user.id)
        user.role = new_role
        db.commit()
        await message.answer(f"Роль успешно изменена на {'соискателя' if new_role == 'job_seeker' else 'работодателя'}. Ваши предыдущие данные удалены.", reply_markup=main_menu)