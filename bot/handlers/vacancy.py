from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from db.database import get_db
from db.queries import get_user_by_telegram_id, get_vacancies_by_user, get_all_categories, create_vacancy
from db.models import Vacancy
from bot.states import CreateVacancy
from bot.keyboards import main_menu

router = Router()

ITEMS_PER_PAGE = 1

def get_vacancy_navigation_keyboard(vacancy_id: int, page: int, total: int):
    kb = []
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"vacancy_page_{page-1}"))
    if page < total - 1:
        nav_row.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"vacancy_page_{page+1}"))
    if nav_row:
        kb.append(nav_row)
    kb.append([InlineKeyboardButton(text="🗑️ Удалить вакансию", callback_data=f"vacancy_delete_{vacancy_id}")])
    kb.append([InlineKeyboardButton(text="➕ Создать новую вакансию", callback_data="vacancy_new")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(F.text == "💼 Мои вакансии")
@router.message(Command("my_vacancies"))
async def my_vacancies(message: Message):
    telegram_id = message.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user or user.role != "employer":
            await message.answer("❌ Эта функция доступна только работодателям.")
            return
        vacancies = get_vacancies_by_user(db, user.id)
        if not vacancies:
            await message.answer(
                "📭 У вас пока нет вакансий.\nСоздайте новую командой /new_vacancy или нажмите кнопку ниже.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Создать вакансию", callback_data="vacancy_new")]
                ])
            )
            return
        page = 0
        vacancy = vacancies[page]
        text = (
            f"📌 *{vacancy.title}* (ID: {vacancy.id})\n\n"
            f"📄 Описание:\n{vacancy.description}\n\n"
            f"🔧 Требования:\n{vacancy.requirements or 'Не указаны'}\n\n"
            f"💰 Зарплата: {vacancy.salary or 'не указана'} руб.\n"
            f"📍 Локация: {vacancy.location or 'не указана'}\n"
            f"📅 Опубликовано: {vacancy.created_at.strftime('%d.%m.%Y')}\n"
            f"🔘 Статус: {'✅ Активна' if vacancy.is_active else '❌ Неактивна'}"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=get_vacancy_navigation_keyboard(vacancy.id, page, len(vacancies)))

@router.callback_query(lambda c: c.data.startswith("vacancy_page_"))
async def navigate_vacancies(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    telegram_id = callback.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user:
            await callback.answer("Пользователь не найден")
            return
        vacancies = get_vacancies_by_user(db, user.id)
        if page < 0 or page >= len(vacancies):
            await callback.answer("Нет вакансий на этой странице")
            return
        vacancy = vacancies[page]
        text = (
            f"📌 *{vacancy.title}* (ID: {vacancy.id})\n\n"
            f"📄 Описание:\n{vacancy.description}\n\n"
            f"🔧 Требования:\n{vacancy.requirements or 'Не указаны'}\n\n"
            f"💰 Зарплата: {vacancy.salary or 'не указана'} руб.\n"
            f"📍 Локация: {vacancy.location or 'не указана'}\n"
            f"📅 Опубликовано: {vacancy.created_at.strftime('%d.%m.%Y')}\n"
            f"🔘 Статус: {'✅ Активна' if vacancy.is_active else '❌ Неактивна'}"
        )
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_vacancy_navigation_keyboard(vacancy.id, page, len(vacancies)))
    await callback.answer()

@router.callback_query(lambda c: c.data == "vacancy_new")
async def new_vacancy_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите название вакансии:")
    await state.set_state(CreateVacancy.title)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("vacancy_delete_"))
async def delete_vacancy_callback(callback: CallbackQuery):
    vacancy_id = int(callback.data.split("_")[2])
    telegram_id = callback.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user or user.role != "employer":
            await callback.answer("❌ Нет прав", show_alert=True)
            return
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id, Vacancy.user_id == user.id).first()
        if not vacancy:
            await callback.answer("Вакансия не найдена", show_alert=True)
            return
        db.delete(vacancy)
        db.commit()
        await callback.answer("✅ Вакансия удалена")
        remaining = get_vacancies_by_user(db, user.id)
        if not remaining:
            await callback.message.edit_text("У вас нет вакансий. Создайте новую с помощью кнопки ниже.",
                                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                 [InlineKeyboardButton(text="➕ Создать вакансию", callback_data="vacancy_new")]
                                             ]))
        else:
            page = 0
            vacancy_new = remaining[page]
            text = f"📌 *{vacancy_new.title}* ..."
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_vacancy_navigation_keyboard(vacancy_new.id, page, len(remaining)))
    await callback.answer()

@router.message(CreateVacancy.title)
async def process_title(message: Message, state: FSMContext) -> None:
    """Обработчик названия вакансии."""
    await state.update_data(title=message.text.strip())

    with next(get_db()) as db:
        categories = get_all_categories(db)
        if not categories:
            await message.answer("⚠️ Категории не найдены. Обратитесь к администратору.")
            await state.clear()
            return

        cats_text = "\n".join([f"{c.id}. {c.name}" for c in categories])
        await message.answer(
            f"Выберите категорию (введите ID):\n\n{cats_text}",
            reply_markup=main_menu  # временно показываем меню, чтобы можно было отменить
        )
    await state.set_state(CreateVacancy.category)


@router.message(CreateVacancy.category)
async def process_category(message: Message, state: FSMContext) -> None:
    """Обработчик выбора категории."""
    try:
        cat_id = int(message.text.strip())
        with next(get_db()) as db:
            categories = get_all_categories(db)
            if not any(c.id == cat_id for c in categories):
                raise ValueError

        await state.update_data(category_id=cat_id)
        await message.answer(
            "📄 Введите описание вакансии (обязанности, условия работы):"
        )
        await state.set_state(CreateVacancy.description)

    except ValueError:
        await message.answer(
            "❌ Неверный ID категории. Пожалуйста, введите число из списка выше."
        )


@router.message(CreateVacancy.description)
async def process_description(message: Message, state: FSMContext) -> None:
    """Обработчик описания вакансии."""
    await state.update_data(description=message.text.strip())
    await message.answer(
        "🔧 Введите требования к кандидату (навыки, опыт, образование):"
    )
    await state.set_state(CreateVacancy.requirements)


@router.message(CreateVacancy.requirements)
async def process_requirements(message: Message, state: FSMContext) -> None:
    """Обработчик требований."""
    await state.update_data(requirements=message.text.strip())
    await message.answer(
        "💰 Введите предлагаемую зарплату (только число в рублях):\n"
        "Например: 80000\n\n"
        "Если зарплата не указана, отправьте 0 или прочерк '-'."
    )
    await state.set_state(CreateVacancy.salary)


@router.message(CreateVacancy.salary)
async def process_salary(message: Message, state: FSMContext) -> None:
    """Обработчик зарплаты."""
    salary_text = message.text.strip()
    try:
        if salary_text in ("-", "0", "не указана"):
            salary = None
        else:
            salary = float(salary_text)
            if salary < 0:
                raise ValueError
        await state.update_data(salary=salary)

        await message.answer(
            "📍 Введите локацию (город, удалёнка, гибрид):\n"
            "Например: Москва, Санкт-Петербург, Удалённо"
        )
        await state.set_state(CreateVacancy.location)

    except ValueError:
        await message.answer(
            "❌ Некорректное число. Введите положительное число или отправьте '-' для пропуска."
        )


@router.message(CreateVacancy.location)
async def process_location(message: Message, state: FSMContext) -> None:
    """Обработчик локации — последний шаг, сохраняем вакансию в БД."""
    location = message.text.strip() or "не указана"
    await state.update_data(location=location)

    data = await state.get_data()
    telegram_id = message.from_user.id

    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user:
            await message.answer("❌ Пользователь не найден. Начните заново с /start.")
            await state.clear()
            return

        try:
            vacancy = create_vacancy(
                db=db,
                user_id=user.id,
                title=data["title"],
                description=data["description"],
                requirements=data["requirements"],
                salary=data.get("salary"),
                location=data["location"],
                category_id=data["category_id"]
            )

            await message.answer(
                f"✅ **Вакансия успешно создана!**\n\n"
                f"📌 Название: {vacancy.title}\n"
                f"💰 Зарплата: {vacancy.salary or 'не указана'} руб.\n"
                f"📍 Локация: {vacancy.location}\n"
                f"🆔 ID вакансии: `{vacancy.id}`\n\n"
                f"Теперь вы можете просматривать отклики на неё в разделе «📩 Отклики».",
                parse_mode="Markdown",
                reply_markup=main_menu
            )
        except Exception as e:
            await message.answer(
                f"⚠️ Ошибка при сохранении вакансии: {str(e)}",
                reply_markup=main_menu
            )
        finally:
            await state.clear()


@router.message(Command("cancel_vacancy"))
async def cancel_vacancy_creation(message: Message, state: FSMContext) -> None:
    """Отмена создания вакансии."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("🤷 Нет активного процесса создания вакансии.")
        return

    await state.clear()
    await message.answer(
        "❌ Создание вакансии отменено.",
        reply_markup=main_menu
    )