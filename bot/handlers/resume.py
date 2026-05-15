from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from db.database import get_db
from db.queries import get_user_by_telegram_id, get_resumes_by_user, get_all_categories, create_resume
from db.models import Resume
from bot.states import CreateResume
from bot.keyboards import main_menu

router = Router()
ITEMS_PER_PAGE = 1

def get_resume_navigation_keyboard(resume_id: int, page: int, total: int):
    """Клавиатура навигации по резюме и удаления"""
    kb = []
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"resume_page_{page-1}"))
    if page < total - 1:
        nav_row.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"resume_page_{page+1}"))
    if nav_row:
        kb.append(nav_row)
    kb.append([InlineKeyboardButton(text="🗑️ Удалить резюме", callback_data=f"resume_delete_{resume_id}")])
    kb.append([InlineKeyboardButton(text="➕ Создать новое резюме", callback_data="resume_new")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(F.text == "📝 Мои резюме")
@router.message(Command("my_resumes"))
async def my_resumes(message: Message):
    telegram_id = message.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user or user.role != "job_seeker":
            await message.answer("❌ Эта функция доступна только соискателям.")
            return
        resumes = get_resumes_by_user(db, user.id)
        if not resumes:
            await message.answer(
                "📭 У вас пока нет резюме.\nСоздайте новое командой /new_resume или нажмите кнопку ниже.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Создать резюме", callback_data="resume_new")]
                ])
            )
            return
        page = 0
        resume = resumes[page]
        text = (
            f"📄 *{resume.title}*\n\n"
            f"📝 Описание:\n{resume.description}\n\n"
            f"🛠️ Навыки: {resume.skills or 'не указаны'}\n"
            f"📆 Опыт: {resume.experience or 'не указан'}\n"
            f"💰 Зарплата: {resume.desired_salary or 'не указана'} руб.\n"
            f"📅 Создано: {resume.created_at.strftime('%d.%m.%Y')}\n"
            f"🔘 Статус: {'✅ Активно' if resume.is_active else '❌ Неактивно'}"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=get_resume_navigation_keyboard(resume.id, page, len(resumes)))

@router.callback_query(lambda c: c.data.startswith("resume_page_"))
async def navigate_resumes(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    telegram_id = callback.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user:
            await callback.answer("Пользователь не найден")
            return
        resumes = get_resumes_by_user(db, user.id)
        if page < 0 or page >= len(resumes):
            await callback.answer("Нет резюме на этой странице")
            return
        resume = resumes[page]
        text = (
            f"📄 *{resume.title}*\n\n"
            f"📝 Описание:\n{resume.description}\n\n"
            f"🛠️ Навыки: {resume.skills or 'не указаны'}\n"
            f"📆 Опыт: {resume.experience or 'не указан'}\n"
            f"💰 Зарплата: {resume.desired_salary or 'не указана'} руб.\n"
            f"📅 Создано: {resume.created_at.strftime('%d.%m.%Y')}\n"
            f"🔘 Статус: {'✅ Активно' if resume.is_active else '❌ Неактивно'}"
        )
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_resume_navigation_keyboard(resume.id, page, len(resumes)))
    await callback.answer()

@router.callback_query(lambda c: c.data == "resume_new")
async def new_resume_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите название резюме:")
    await state.set_state(CreateResume.title)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("resume_delete_"))
async def delete_resume_callback(callback: CallbackQuery):
    resume_id = int(callback.data.split("_")[2])
    telegram_id = callback.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user or user.role != "job_seeker":
            await callback.answer("❌ Нет прав", show_alert=True)
            return
        resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
        if not resume:
            await callback.answer("Резюме не найдено", show_alert=True)
            return
        db.delete(resume)
        db.commit()
        await callback.answer("✅ Резюме удалено")
        remaining = get_resumes_by_user(db, user.id)
        if not remaining:
            await callback.message.edit_text("У вас нет резюме. Создайте новое с помощью кнопки ниже.",
                                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                 [InlineKeyboardButton(text="➕ Создать резюме", callback_data="resume_new")]
                                             ]))
        else:
            page = 0
            resume_new = remaining[page]
            text = (
                f"📄 *{resume_new.title}*\n\n"
                f"📝 Описание:\n{resume_new.description}\n\n"
                f"🛠️ Навыки: {resume_new.skills or 'не указаны'}\n"
                f"📆 Опыт: {resume_new.experience or 'не указан'}\n"
                f"💰 Зарплата: {resume_new.desired_salary or 'не указана'} руб.\n"
                f"📅 Создано: {resume_new.created_at.strftime('%d.%m.%Y')}\n"
                f"🔘 Статус: {'✅ Активно' if resume_new.is_active else '❌ Неактивно'}"
            )
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_resume_navigation_keyboard(resume_new.id, page, len(remaining)))
    await callback.answer()

# ------------------- ОБРАБОТЧИКИ СОЗДАНИЯ РЕЗЮМЕ (FSM) -------------------
@router.message(Command("new_resume"))
async def new_resume_start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user or user.role != "job_seeker":
            await message.answer("❌ Только соискатели могут создавать резюме.")
            return
    await state.set_state(CreateResume.title)
    await message.answer("Введите название резюме:", reply_markup=main_menu)

@router.message(CreateResume.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    with next(get_db()) as db:
        categories = get_all_categories(db)
        if not categories:
            await message.answer("⚠️ Категории не найдены.")
            return
        cats_text = "\n".join([f"{c.id}. {c.name}" for c in categories])
        await message.answer(f"Выберите категорию (введите ID):\n{cats_text}")
    await state.set_state(CreateResume.category)

@router.message(CreateResume.category)
async def process_category(message: Message, state: FSMContext):
    try:
        cat_id = int(message.text)
        with next(get_db()) as db:
            categories = get_all_categories(db)
            if not any(c.id == cat_id for c in categories):
                raise ValueError
        await state.update_data(category_id=cat_id)
        await message.answer("Введите описание резюме (ваш опыт, навыки):")
        await state.set_state(CreateResume.description)
    except ValueError:
        await message.answer("❌ Неверный ID категории. Попробуйте снова.")

@router.message(CreateResume.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Перечислите ключевые навыки через запятую:")
    await state.set_state(CreateResume.skills)

@router.message(CreateResume.skills)
async def process_skills(message: Message, state: FSMContext):
    await state.update_data(skills=message.text)
    await message.answer("Опишите ваш опыт работы (места, годы):")
    await state.set_state(CreateResume.experience)

@router.message(CreateResume.experience)
async def process_experience(message: Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await message.answer("Желаемая зарплата (в рублях):")
    await state.set_state(CreateResume.salary)

@router.message(CreateResume.salary)
async def process_salary(message: Message, state: FSMContext):
    try:
        salary = float(message.text)
        data = await state.get_data()
        telegram_id = message.from_user.id
        with next(get_db()) as db:
            user = get_user_by_telegram_id(db, telegram_id)
            if not user:
                await message.answer("Сначала зарегистрируйтесь /start")
                await state.clear()
                return
            create_resume(db, user.id, data["title"], data["description"],
                          data["skills"], data["experience"], salary, data["category_id"])
        await message.answer("✅ Резюме успешно создано!", reply_markup=main_menu)
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число (зарплату).")