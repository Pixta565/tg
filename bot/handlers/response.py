from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from db.database import get_db
from db.queries import (
    get_user_by_telegram_id,
    filter_vacancies_by_category,
    filter_resumes_by_category,
    get_all_categories,
    get_responses_for_resume,
    get_responses_for_vacancy,
    update_response_status,
    create_response,
    get_resumes_by_user
)
from db.models import Category, Vacancy, Response, Resume
from bot.keyboards import main_menu, vacancy_action_buttons, response_status_buttons, resume_action_buttons

router = Router()

ITEMS_PER_PAGE = 5

def make_vacancy_list_markup(vacancies: list, page: int, total_pages: int, category_id: int):
    kb = []
    for vac in vacancies:
        kb.append([InlineKeyboardButton(
            text=f"📩 Откликнуться: {vac.title[:30]}",
            callback_data=f"apply_{vac.id}"
        )])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"vac_page_{category_id}_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"vac_page_{category_id}_{page+1}"))
    if nav_buttons:
        kb.append(nav_buttons)
    kb.append([InlineKeyboardButton(text="◀️ Назад к категориям", callback_data="back_to_categories_vacancy")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def make_resume_list_markup(resumes: list, page: int, total_pages: int, category_id: int):
    kb = []
    for res in resumes:
        kb.append([InlineKeyboardButton(
            text=f"📩 Пригласить: {res.title[:30]}",
            callback_data=f"invite_{res.id}"
        )])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"res_page_{category_id}_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"res_page_{category_id}_{page+1}"))
    if nav_buttons:
        kb.append(nav_buttons)
    kb.append([InlineKeyboardButton(text="◀️ Назад к категориям", callback_data="back_to_categories_resume")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --------------------- ПОИСК ВАКАНСИЙ ---------------------
@router.message(F.text == "🔍 Поиск вакансий")
async def search_vacancies_by_category_start(message: Message):
    telegram_id = message.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user:
            await message.answer("Сначала зарегистрируйтесь через /start")
            return
        if user.role != "job_seeker":
            await message.answer("❌ Поиск вакансий доступен только соискателям.")
            return
        categories = get_all_categories(db)
        if not categories:
            await message.answer("⚠️ Категории не найдены.")
            return
        text = "🔍 *Выберите категорию для поиска вакансий:*"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"show_vacancies_{cat.id}")] for cat in categories
        ])
        await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@router.callback_query(lambda c: c.data.startswith("show_vacancies_"))
async def show_vacancies_by_category(callback: CallbackQuery):
    category_id = int(callback.data.split("_")[2])
    with next(get_db()) as db:
        vacancies = filter_vacancies_by_category(db, category_id)
        category = db.query(Category).filter(Category.id == category_id).first()
        category_name = category.name if category else "неизвестная"
        if not vacancies:
            await callback.message.edit_text(f"😕 В категории «{category_name}» нет активных вакансий.")
            return
        total_pages = (len(vacancies) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        page = 0
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        page_vacancies = vacancies[start:end]
        text = f"🏷️ *Вакансии в категории «{category_name}» (страница {page+1}/{total_pages}):*\n\n"
        for vac in page_vacancies:
            text += f"• *{vac.title}* (ID: {vac.id})\n💰 {vac.salary or 'не указана'} руб.\n📍 {vac.location or 'не указана'}\n\n"
        markup = make_vacancy_list_markup(page_vacancies, page, total_pages, category_id)
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("vac_page_"))
async def paginate_vacancies(callback: CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) >= 4:
        category_id = int(parts[2])
        page = int(parts[3])
    else:
        await callback.answer("Ошибка: неверный формат данных")
        return
    with next(get_db()) as db:
        vacancies = filter_vacancies_by_category(db, category_id)
        category = db.query(Category).filter(Category.id == category_id).first()
        category_name = category.name if category else "неизвестная"
        if not vacancies:
            await callback.message.edit_text(f"😕 В категории «{category_name}» нет активных вакансий.")
            return
        total_pages = (len(vacancies) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        page_vacancies = vacancies[start:end]
        text = f"🏷️ *Вакансии в категории «{category_name}» (страница {page+1}/{total_pages}):*\n\n"
        for vac in page_vacancies:
            text += f"• *{vac.title}* (ID: {vac.id})\n💰 {vac.salary or 'не указана'} руб.\n📍 {vac.location or 'не указана'}\n\n"
        markup = make_vacancy_list_markup(page_vacancies, page, total_pages, category_id)
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
    await callback.answer()

# --------------------- ПОИСК СОИСКАТЕЛЕЙ ---------------------
@router.message(F.text == "🔍 Поиск соискателей")
@router.message(Command("search_candidates"))
async def search_candidates_by_category_start(message: Message):
    telegram_id = message.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user or user.role != "employer":
            await message.answer("❌ Эта функция доступна только работодателям.")
            return
        categories = get_all_categories(db)
        if not categories:
            await message.answer("⚠️ Категории не найдены.")
            return
        text = "👥 *Выберите категорию для поиска соискателей:*"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"show_resumes_{cat.id}")] for cat in categories
        ])
        await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@router.callback_query(lambda c: c.data.startswith("show_resumes_"))
async def show_resumes_by_category(callback: CallbackQuery):
    category_id = int(callback.data.split("_")[2])
    with next(get_db()) as db:
        resumes = filter_resumes_by_category(db, category_id)
        category = db.query(Category).filter(Category.id == category_id).first()
        category_name = category.name if category else "неизвестная"
        if not resumes:
            await callback.message.edit_text(f"😕 В категории «{category_name}» нет активных резюме.")
            return
        total_pages = (len(resumes) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        page = 0
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        page_resumes = resumes[start:end]
        text = f"👥 *Соискатели в категории «{category_name}» (страница {page+1}/{total_pages}):*\n\n"
        for res in page_resumes:
            text += f"• *{res.title}* (ID: {res.id})\n👤 {res.user.first_name}\n💰 {res.desired_salary or 'не указана'} руб.\n🛠️ {res.skills or 'не указаны'}\n\n"
        markup = make_resume_list_markup(page_resumes, page, total_pages, category_id)
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("res_page_"))
async def paginate_resumes(callback: CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) >= 4:
        category_id = int(parts[2])
        page = int(parts[3])
    else:
        await callback.answer("Ошибка: неверный формат данных")
        return
    with next(get_db()) as db:
        resumes = filter_resumes_by_category(db, category_id)
        category = db.query(Category).filter(Category.id == category_id).first()
        category_name = category.name if category else "неизвестная"
        if not resumes:
            await callback.message.edit_text(f"😕 В категории «{category_name}» нет активных резюме.")
            return
        total_pages = (len(resumes) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        page_resumes = resumes[start:end]
        text = f"👥 *Соискатели в категории «{category_name}» (страница {page+1}/{total_pages}):*\n\n"
        for res in page_resumes:
            text += f"• *{res.title}* (ID: {res.id})\n👤 {res.user.first_name}\n💰 {res.desired_salary or 'не указана'} руб.\n🛠️ {res.skills or 'не указаны'}\n\n"
        markup = make_resume_list_markup(page_resumes, page, total_pages, category_id)
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
    await callback.answer()

# --------------------- КНОПКИ НАЗАД К КАТЕГОРИЯМ ---------------------
@router.callback_query(lambda c: c.data == "back_to_categories_vacancy")
async def back_to_vacancy_categories(callback: CallbackQuery):
    with next(get_db()) as db:
        categories = get_all_categories(db)
        if not categories:
            await callback.message.edit_text("⚠️ Категории не найдены.")
            return
        text = "🔍 *Выберите категорию для поиска вакансий:*"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"show_vacancies_{cat.id}")] for cat in categories
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

@router.callback_query(lambda c: c.data == "back_to_categories_resume")
async def back_to_resume_categories(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user or user.role != "employer":
            await callback.message.edit_text("❌ Эта функция доступна только работодателям.")
            return
        categories = get_all_categories(db)
        if not categories:
            await callback.message.edit_text("⚠️ Категории не найдены.")
            return
        text = "👥 *Выберите категорию для поиска соискателей:*"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"show_resumes_{cat.id}")] for cat in categories
        ])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

# --------------------- ОТКЛИК НА ВАКАНСИЮ (ДЛЯ СОИСКАТЕЛЯ) ---------------------
@router.callback_query(lambda c: c.data.startswith("apply_"))
async def apply_to_vacancy(callback: CallbackQuery):
    vacancy_id = int(callback.data.split("_")[1])
    telegram_id = callback.from_user.id

    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user or user.role != "job_seeker":
            await callback.answer("❌ Только соискатели могут откликаться!", show_alert=True)
            return

        resumes = get_resumes_by_user(db, user.id)
        if not resumes:
            await callback.answer("❌ У вас нет резюме. Создайте его через /new_resume", show_alert=True)
            return

        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        if not vacancy:
            await callback.answer("❌ Вакансия не найдена", show_alert=True)
            return

        if len(resumes) == 1:
            resume = resumes[0]
            existing = db.query(Response).filter(
                Response.resume_id == resume.id,
                Response.vacancy_id == vacancy.id
            ).first()
            if existing:
                await callback.answer("Вы уже откликались на эту вакансию!", show_alert=True)
                return
            create_response(db, resume.id, vacancy.id)
            await callback.answer("✅ Отклик отправлен!", show_alert=True)
            await callback.message.answer(f"Вы откликнулись на вакансию «{vacancy.title}».")
            
            # Уведомление работодателю
            employer_id = vacancy.user.telegram_id
            try:
                await callback.bot.send_message(
                    employer_id,
                    f"📢 *Новый отклик!*\n\n"
                    f"Соискатель *{user.first_name}* откликнулся на вашу вакансию *{vacancy.title}*.\n"
                    f"Проверьте отклики в меню.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Не удалось отправить уведомление работодателю {employer_id}: {e}")
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=r.title, callback_data=f"choose_resume_{r.id}_{vacancy_id}")] for r in resumes
            ])
            await callback.message.answer("Выберите резюме для отклика:", reply_markup=kb)
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("choose_resume_"))
async def choose_resume_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    resume_id = int(parts[2])
    vacancy_id = int(parts[3])

    with next(get_db()) as db:
        existing = db.query(Response).filter(
            Response.resume_id == resume_id,
            Response.vacancy_id == vacancy_id
        ).first()
        if existing:
            await callback.answer("Вы уже откликались на эту вакансию данным резюме!", show_alert=True)
            return
        create_response(db, resume_id, vacancy_id)
        await callback.answer("✅ Отклик отправлен!", show_alert=True)
        await callback.message.edit_reply_markup()
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        await callback.message.answer(f"Вы откликнулись на вакансию «{vacancy.title}».")
        
        employer_id = vacancy.user.telegram_id
        try:
            await callback.bot.send_message(
                employer_id,
                f"📢 *Новый отклик!*\n\n"
                f"Соискатель *{resume.user.first_name}* откликнулся на вашу вакансию *{vacancy.title}*.\n"
                f"Проверьте отклики в меню.",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление работодателю {employer_id}: {e}")
    await callback.answer()

# --------------------- ПРИГЛАШЕНИЕ СОИСКАТЕЛЯ (ДЛЯ РАБОТОДАТЕЛЯ) ---------------------
@router.callback_query(lambda c: c.data.startswith("invite_"))
async def invite_candidate(callback: CallbackQuery):
    resume_id = int(callback.data.split("_")[1])
    telegram_id = callback.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user or user.role != "employer":
            await callback.answer("❌ Только работодатели могут приглашать!", show_alert=True)
            return
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            await callback.answer("❌ Резюме не найдено", show_alert=True)
            return
        
        seeker_id = resume.user.telegram_id
        try:
            await callback.bot.send_message(
                seeker_id,
                f"🎉 *Вам пришло приглашение на работу!*\n\n"
                f"Работодатель *{user.first_name}* заинтересовался вашим резюме *{resume.title}*.\n"
                f"Свяжитесь с ним для дальнейших шагов.",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Не удалось отправить приглашение соискателю {seeker_id}: {e}")
        
        await callback.answer(f"✅ Приглашение отправлено соискателю {resume.user.first_name}!", show_alert=True)
    await callback.answer()

# --------------------- ПРОСМОТР ОТКЛИКОВ ---------------------
@router.message(F.text == "📩 Отклики")
async def my_responses(message: Message):
    telegram_id = message.from_user.id
    with next(get_db()) as db:
        user = get_user_by_telegram_id(db, telegram_id)
        if not user:
            await message.answer("Сначала зарегистрируйтесь /start")
            return
        
        if user.role == "job_seeker":
            resumes = get_resumes_by_user(db, user.id)
            if not resumes:
                await message.answer("У вас нет резюме. Создайте через /new_resume")
                return
            text = "📨 Ваши отклики:\n\n"
            for resume in resumes:
                responses = get_responses_for_resume(db, resume.id)
                for resp in responses:
                    vac = resp.vacancy
                    status_emoji = "⏳" if resp.status == "pending" else ("✅" if resp.status == "accepted" else "❌")
                    status_text = {
                        "pending": "Ожидает",
                        "accepted": "Принят",
                        "rejected": "Отклонён"
                    }.get(resp.status, resp.status)
                    text += f"{status_emoji} Резюме «{resume.title}» → Вакансия «{vac.title}»: {status_text}\n"
            await message.answer(text if len(text) > 20 else "Нет откликов.")
        else:
            vacancies = user.vacancies
            if not vacancies:
                await message.answer("У вас нет вакансий.")
                return
            for vac in vacancies:
                responses = get_responses_for_vacancy(db, vac.id)
                for resp in responses:
                    resume = resp.resume
                    status_text = {
                        "pending": "Ожидает",
                        "accepted": "Принят",
                        "rejected": "Отклонён"
                    }.get(resp.status, resp.status)
                    await message.answer(
                        f"Отклик на вакансию «{vac.title}» от {resume.user.first_name} (статус: {status_text})",
                        reply_markup=response_status_buttons(resp.id)
                    )
            if not any(get_responses_for_vacancy(db, v.id) for v in vacancies):
                await message.answer("Нет откликов на ваши вакансии.")

@router.callback_query(lambda c: c.data.startswith("accept_"))
async def accept_response(callback: CallbackQuery):
    response_id = int(callback.data.split("_")[1])
    with next(get_db()) as db:
        update_response_status(db, response_id, "accepted")
    await callback.answer("✅ Отклик принят!")
    await callback.message.edit_reply_markup()

@router.callback_query(lambda c: c.data.startswith("reject_"))
async def reject_response(callback: CallbackQuery):
    response_id = int(callback.data.split("_")[1])
    with next(get_db()) as db:
        update_response_status(db, response_id, "rejected")
    await callback.answer("❌ Отклик отклонён.")
    await callback.message.edit_reply_markup()