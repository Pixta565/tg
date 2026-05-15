"""
Скрипт для заполнения базы данных тестовыми данными (добавление без удаления).
Запуск: python -m db.seed
"""

import random
from db.database import SessionLocal, init_db
from db.models import User, Category, Resume, Vacancy, Response
from db.queries import get_all_categories, create_user, create_resume, create_vacancy, create_response

# ------------------- ДАННЫЕ ДЛЯ ГЕНЕРАЦИИ -------------------
# Категории (10 штук)
CATEGORIES = [
    "IT", "Маркетинг", "Продажи", "Дизайн", "Управление",
    "Строительство", "Логистика", "Финансы", "Образование", "Медицина"
]

# Шаблоны вакансий по категориям (по 15 штук)
VACANCY_TEMPLATES = {
    "IT": [
        "Python разработчик", "Java разработчик", "Frontend разработчик", "Backend разработчик",
        "DevOps инженер", "Data Scientist", "Аналитик данных", "Менеджер проектов IT",
        "UI/UX дизайнер", "Системный администратор", "QA инженер", "Маркетолог IT",
        "Продакт-менеджер", "iOS разработчик", "Android разработчик"
    ],
    "Маркетинг": [
        "SEO-специалист", "SMM-менеджер", "Контент-маркетолог", "PR-менеджер", "Email-маркетолог",
        "Маркетолог-аналитик", "Бренд-менеджер", "Product-маркетолог", "Таргетолог", "Медиабайер",
        "Копирайтер", "Маркетолог по автоматизации", "Event-маркетолог", "Digital-маркетолог", "Growth-менеджер"
    ],
    "Продажи": [
        "Менеджер по продажам", "Аккаунт-менеджер", "Специалист по работе с клиентами", "Руководитель отдела продаж",
        "Sales-менеджер", "Торговый представитель", "Менеджер по развитию бизнеса", "Key Account Manager",
        "Менеджер по продажам B2B", "Менеджер по продажам B2C", "Sales Development Representative",
        "Customer Success", "Sales Engineer", "Специалист по холодным продажам", "Телемаркетолог"
    ],
    "Дизайн": [
        "Графический дизайнер", "UI/UX дизайнер", "Веб-дизайнер", "Моушн-дизайнер", "3D-дизайнер",
        "Гейм-дизайнер", "Промышленный дизайнер", "Дизайнер интерьеров", "Ландшафтный дизайнер", "Типограф",
        "Дизайнер упаковки", "Бренд-дизайнер", "Продуктовый дизайнер", "Арт-директор", "Дизайнер презентаций"
    ],
    "Управление": [
        "Project Manager", "Product Manager", "Team Lead", "HR-менеджер", "Операционный директор",
        "Руководитель отдела", "CEO", "COO", "CTO", "CFO",
        "Специалист по управлению персоналом", "Business Analyst", "Scrum-мастер", "Agile-коуч", "Управляющий проектами"
    ],
    "Строительство": [
        "Прораб", "Инженер ПТО", "Мастер СМР", "Монтажник", "Кладовщик на стройку",
        "Строитель-отделочник", "Арматурщик", "Бетонщик", "Сварщик", "Электромонтажник",
        "Сантехник", "Геодезист", "Начальник участка", "Сметчик", "Архитектор"
    ],
    "Логистика": [
        "Менеджер по логистике", "Диспетчер", "Водитель-экспедитор", "Специалист по таможенному оформлению",
        "Кладовщик", "Оператор склада", "Комплектовщик", "Начальник склада", "Логист-аналитик",
        "Специалист по ВЭД", "Транспортный логист", "Складской работник", "Экспедитор",
        "Менеджер по цепочкам поставок", "Оператор ПК на складе"
    ],
    "Финансы": [
        "Бухгалтер", "Финансовый аналитик", "Экономист", "Аудитор", "Налоговый консультант",
        "Финансовый менеджер", "Инвестиционный аналитик", "Казначей", "Кредитный специалист",
        "Специалист по МСФО", "Финансовый контролер", "Бухгалтер-калькулятор", "Специалист по банкротству",
        "Риск-менеджер", "Страховой брокер"
    ],
    "Образование": [
        "Преподаватель", "Учитель", "Методист", "Педагог-психолог", "Репетитор",
        "Тьютор", "Преподаватель английского", "Преподаватель программирования", "Ассистент преподавателя",
        "Декан", "Менеджер по образовательным программам", "Научный сотрудник", "Куратор курсов",
        "Онлайн-преподаватель", "Специалист по ЕГЭ"
    ],
    "Медицина": [
        "Врач-терапевт", "Медицинская сестра", "Фармацевт", "Лаборант", "Санитарка",
        "Стоматолог", "Педиатр", "Хирург", "Медицинский представитель", "Рентген-лаборант",
        "Физиотерапевт", "Ветеринар", "Психолог", "Логопед", "Администратор медицинского центра"
    ]
}

# Дополнительные медицинские вакансии для нового работодателя (опционально)
MEDICAL_VACANCIES = [
    "Врач скорой помощи", "Медбрат/медсестра в стационар", "Санитар в операционную", "Фельдшер",
    "Акушерка", "Медицинский регистратор", "Сиделка (патронажная служба)", "Косметолог",
    "Зубной техник", "Провизор в аптеку"
]

# Вспомогательные списки для генерации описаний
SKILLS_LIST = [
    "Python, Django, Flask", "Java, Spring, Hibernate", "JavaScript, React, Vue", "SQL, PostgreSQL, MongoDB",
    "Docker, Kubernetes, CI/CD", "Pandas, NumPy, ML", "Excel, Tableau, PowerBI", "Agile, Scrum, Jira",
    "Figma, Photoshop, Sketch", "Linux, Bash, Networking", "Selenium, pytest", "SEO, SMM, PPC"
]
EXPERIENCE_TEXTS = [
    "1 год коммерческой разработки", "3 года в IT-компании", "5 лет веб-разработки",
    "Опыт работы с высоконагруженными системами", "Участие в 10+ проектах", "Работал в стартапе"
]
DESCRIPTIONS = [
    "Ответственный, коммуникабельный, быстро учусь.", "Люблю решать сложные задачи.",
    "Командный игрок.", "Ищу интересный проект для профессионального роста.",
    "Умею работать с большим объёмом информации."
]
LOCATIONS = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
             "Нижний Новгород", "Удалённо", "Сочи", "Краснодар"]

# ------------------- СПИСОК ПОЛЬЗОВАТЕЛЕЙ (из вашей таблицы) -------------------
# Формат: (telegram_id, username, first_name, role)
USERS = [
    (229673657, "egorkas16", "Строительная Компания", "employer"),   # основной работодатель
    # Соискатели (45 человек)
    (100000001, "кристина_алексеев_1", "Кристина Алексеев", "job_seeker"),
    (100000002, "кристина_морозов_2", "Кристина Морозов", "job_seeker"),
    (100000003, "максим_волков_3", "Максим Волков", "job_seeker"),
    (100000004, "виктор_алексеев_4", "Виктор Алексеев", "job_seeker"),
    (100000005, "виктор_алексеев_5", "Виктор Алексеев", "job_seeker"),
    (100000006, "александра_егоров_6", "Александра Егоров", "job_seeker"),
    (100000007, "ольга_егоров_7", "Ольга Егоров", "job_seeker"),
    (100000008, "виктор_козлов_8", "Виктор Козлов", "job_seeker"),
    (100000009, "владимир_егоров_9", "Владимир Егоров", "job_seeker"),
    (100000010, "мария_васильев_10", "Мария Васильев", "job_seeker"),
    (100000011, "иван_новиков_11", "Иван Новиков", "job_seeker"),
    (100000012, "елена_кузнецов_12", "Елена Кузнецов", "job_seeker"),
    (100000013, "павел_смирнов_13", "Павел Смирнов", "job_seeker"),
    (100000014, "максим_павлов_14", "Максим Павлов", "job_seeker"),
    (100000015, "павел_степанов_15", "Павел Степанов", "job_seeker"),
    (100000016, "андрей_фёдоров_16", "Андрей Фёдоров", "job_seeker"),
    (100000017, "дмитрий_михайлов_17", "Дмитрий Михайлов", "job_seeker"),
    (100000018, "александра_михайлов_18", "Александра Михайлов", "job_seeker"),
    (100000019, "мария_захаров_19", "Мария Захаров", "job_seeker"),
    (100000020, "максим_николаев_20", "Максим Николаев", "job_seeker"),
    (100000021, "павел_лебедев_21", "Павел Лебедев", "job_seeker"),
    (100000022, "максим_николаев_22", "Максим Николаев", "job_seeker"),
    (100000023, "елена_соловьёв_23", "Елена Соловьёв", "job_seeker"),
    (100000024, "владимир_морозов_24", "Владимир Морозов", "job_seeker"),
    (100000025, "александра_андреев_25", "Александра Андреев", "job_seeker"),
    (100000026, "татьяна_михайлов_26", "Татьяна Михайлов", "job_seeker"),
    (100000027, "екатерина_кузнецов_27", "Екатерина Кузнецов", "job_seeker"),
    (100000028, "светлана_кузнецов_28", "Светлана Кузнецов", "job_seeker"),
    (100000029, "валентина_орлов_29", "Валентина Орлов", "job_seeker"),
    (100000030, "максим_семёнов_30", "Максим Семёнов", "job_seeker"),
    (100000031, "людмила_волков_31", "Людмила Волков", "job_seeker"),
    (100000032, "кристина_алексеев_32", "Кристина Алексеев", "job_seeker"),
    (100000033, "максим_соловьёв_33", "Максим Соловьёв", "job_seeker"),
    (100000034, "павел_козлов_34", "Павел Козлов", "job_seeker"),
    (100000035, "наталья_тимофеев_35", "Наталья Тимофеев", "job_seeker"),
    (100000036, "кристина_николаев_36", "Кристина Николаев", "job_seeker"),
    (100000037, "вячеслав_новиков_37", "Вячеслав Новиков", "job_seeker"),
    (100000038, "мария_васильев_38", "Мария Васильев", "job_seeker"),
    (100000039, "елена_новиков_39", "Елена Новиков", "job_seeker"),
    (100000040, "павел_морозов_40", "Павел Морозов", "job_seeker"),
    (100000041, "александра_тимофеев_41", "Александра Тимофеев", "job_seeker"),
    (100000042, "павел_тимофеев_42", "Павел Тимофеев", "job_seeker"),
    (100000043, "анна_соловьёв_43", "Анна Соловьёв", "job_seeker"),
    (100000044, "сергей_андреев_44", "Сергей Андреев", "job_seeker"),
    (100000045, "галина_фёдоров_45", "Галина Фёдоров", "job_seeker"),
]

# Дополнительные компании (5 штук) – работодатели
COMPANIES = [
    (100000100, "company_alfa", "Альфа-Групп", "employer"),
    (100000101, "company_beta", "Бета-Строй", "employer"),
    (100000102, "company_gamma", "Гамма-Логистик", "employer"),
    (100000103, "company_delta", "Дельта-Медика", "employer"),
    (100000104, "company_omega", "Омега-Финанс", "employer"),
]

# ... (все предыдущие импорты и данные до функции seed_database остаются без изменений)

def seed_database():
    init_db()
    db = SessionLocal()

    try:
        # 1. Категории (без изменений)
        existing_cats = {c.name for c in db.query(Category).all()}
        for cat_name in CATEGORIES:
            if cat_name not in existing_cats:
                db.add(Category(name=cat_name))
        db.commit()
        categories = db.query(Category).all()
        print(f"✅ Категорий в БД: {len(categories)}")

        # 2. Создаём всех пользователей из списка USERS (основной работодатель + соискатели)
        for telegram_id, username, first_name, role in USERS:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                create_user(db, telegram_id, username, first_name, role)
                print(f"✅ Создан пользователь: {first_name} ({role})")
            else:
                print(f"ℹ️ Пользователь {first_name} уже существует")

        # 3. Создаём дополнительных работодателей (компании)
        for telegram_id, username, first_name, role in COMPANIES:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                create_user(db, telegram_id, username, first_name, role)
                print(f"✅ Создана компания: {first_name}")
            else:
                print(f"ℹ️ Компания {first_name} уже существует")

        # Получаем всех работодателей (основной + компании)
        employer_main = db.query(User).filter(User.telegram_id == 229673657).first()
        if not employer_main:
            print("⚠️ Основной работодатель не найден, пропускаем создание вакансий")
            employer_main = None

        # Собираем всех работодателей, которым будем создавать вакансии
        employer_ids = [employer_main.id] if employer_main else []
        for _, _, _, _ in COMPANIES:
            # ищем по telegram_id, но проще достать из БД
            pass
        # Альтернатива: получить всех работодателей с telegram_id из COMPANIES и основного
        employer_objects = []
        if employer_main:
            employer_objects.append(employer_main)
        for comp in COMPANIES:
            comp_user = db.query(User).filter(User.telegram_id == comp[0]).first()
            if comp_user:
                employer_objects.append(comp_user)
        if not employer_objects:
            print("⚠️ Нет работодателей для создания вакансий")
        else:
            # 4. Удаляем старые вакансии, созданные этими работодателями (чтобы не дублировать)
            employer_ids = [e.id for e in employer_objects]
            deleted_vacancies = db.query(Vacancy).filter(Vacancy.user_id.in_(employer_ids)).delete()
            print(f"🗑️ Удалено старых вакансий у этих работодателей: {deleted_vacancies}")
            db.commit()

            # 5. Создаём новые вакансии, распределяя между работодателями (50% основному, 50% остальным)
            cat_dict = {c.name: c for c in categories}
            all_vacancy_titles = []
            for cat_name, titles in VACANCY_TEMPLATES.items():
                for title in titles[:15]:
                    all_vacancy_titles.append((cat_name, title))

            # Перемешиваем вакансии, чтобы распределение было случайным
            random.shuffle(all_vacancy_titles)
            total_vacancies = len(all_vacancy_titles)  # должно быть 150
            # Определяем, сколько вакансий отдать основному работодателю (50%)
            main_count = total_vacancies // 2
            other_count = total_vacancies - main_count

            # Распределяем вакансии
            main_vacancies = all_vacancy_titles[:main_count]
            other_vacancies = all_vacancy_titles[main_count:]

            # Создаём вакансии для основного работодателя
            for cat_name, title in main_vacancies:
                category = cat_dict.get(cat_name)
                if not category:
                    continue
                create_vacancy(
                    db, employer_main.id, title,
                    random.choice(DESCRIPTIONS),
                    random.choice(SKILLS_LIST),
                    random.choice([50000, 70000, 90000, 120000]),
                    random.choice(LOCATIONS),
                    category.id
                )
            print(f"✅ Создано {len(main_vacancies)} вакансий для основного работодателя")

            # Создаём вакансии для остальных компаний (равномерно распределяем)
            other_employers = [e for e in employer_objects if e.id != employer_main.id]
            if other_employers:
                # Распределяем other_vacancies по кругу между other_employers
                for idx, (cat_name, title) in enumerate(other_vacancies):
                    employer = other_employers[idx % len(other_employers)]
                    category = cat_dict.get(cat_name)
                    if not category:
                        continue
                    create_vacancy(
                        db, employer.id, title,
                        random.choice(DESCRIPTIONS),
                        random.choice(SKILLS_LIST),
                        random.choice([50000, 70000, 90000, 120000]),
                        random.choice(LOCATIONS),
                        category.id
                    )
                print(f"✅ Создано {len(other_vacancies)} вакансий для дополнительных компаний")
            else:
                print("⚠️ Нет дополнительных компаний, все вакансии отданы основному")

        # 6. Резюме для всех соискателей (без изменений)
        seekers = db.query(User).filter(User.role == "job_seeker").all()
        for seeker in seekers:
            existing = db.query(Resume).filter(Resume.user_id == seeker.id).first()
            if not existing:
                category = random.choice(categories)
                create_resume(
                    db, seeker.id, f"Резюме {seeker.first_name.split()[0]}",
                    random.choice(DESCRIPTIONS),
                    random.choice(SKILLS_LIST),
                    random.choice(EXPERIENCE_TEXTS),
                    random.choice([40000, 60000, 80000, 100000]),
                    category.id
                )
        print("✅ Резюме для соискателей проверены/добавлены")

        # 7. Отклики – удаляем старые, создаём не более 1 отклика на резюме
        deleted = db.query(Response).delete()
        print(f"🗑️ Удалено старых откликов: {deleted}")
        db.commit()

        all_vacancies = db.query(Vacancy).all()
        resumes = db.query(Resume).all()
        responses_created = 0
        for resume in resumes:
            needed = 1
            candidates = [v for v in all_vacancies]
            if len(candidates) > 0:
                chosen = random.sample(candidates, min(needed, len(candidates)))
                for vacancy in chosen:
                    create_response(db, resume.id, vacancy.id)
                    responses_created += 1
        print(f"✅ Создано новых откликов: {responses_created}")

        # Итоговая статистика
        print("\n=== СТАТИСТИКА БАЗЫ ДАННЫХ ===")
        print(f"Пользователей: {db.query(User).count()} (соискателей: {db.query(User).filter(User.role == 'job_seeker').count()}, работодателей: {db.query(User).filter(User.role == 'employer').count()})")
        print(f"Категорий: {db.query(Category).count()}")
        print(f"Резюме: {db.query(Resume).count()}")
        print(f"Вакансий: {db.query(Vacancy).count()}")
        print(f"Откликов: {db.query(Response).count()}")
        print("=== Заполнение завершено ===")

    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()