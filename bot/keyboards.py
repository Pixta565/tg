from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Мои резюме"), KeyboardButton(text="💼 Мои вакансии")],
        [KeyboardButton(text="🔍 Поиск вакансий"), KeyboardButton(text="🔍 Поиск соискателей")],
        [KeyboardButton(text="📩 Отклики"), KeyboardButton(text="⚙️ Сменить роль")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)

role_choice = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Соискатель")],
        [KeyboardButton(text="🏢 Работодатель")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

def response_status_buttons(response_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{response_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{response_id}")
        ]
    ])

def vacancy_action_buttons(vacancy_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Откликнуться", callback_data=f"apply_{vacancy_id}")]
    ])

def category_buttons(categories, prefix="cat_vacancy"):
    kb = []
    for cat in categories:
        kb.append([InlineKeyboardButton(text=cat.name, callback_data=f"{prefix}_{cat.id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def resume_action_buttons(resume_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Пригласить", callback_data=f"invite_{resume_id}")]
    ])

def back_button(back_type: str):
    """back_type = 'vacancy' или 'resume'"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к категориям", callback_data=f"back_{back_type}")]
    ])