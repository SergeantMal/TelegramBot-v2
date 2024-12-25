# TelegramBot_v2 - это продвинутый бот для управления задачами, реализованный на Python с использованием библиотеки telebot.
# Он позволяет пользователям создавать, редактировать, удалить и отправлять напоминания по задачам.
# Пользователи могут установить приоритет, категорию, дату выполнения и напоминание.


# Импорт библиотек

import telebot
import datetime
import time
import threading
import csv
import os
import schedule
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

logging.basicConfig(filename='bot.log', level=logging.DEBUG)

bot = telebot.TeleBot('ADD_YOUR_TOKEN', parse_mode='HTML')

TASKS_FILE = 'task.csv'
USERS_FILE = 'users.csv'

PRIORITY_EMOJIS = {
    'Высокий': '🔴',
    'Средний': '🟠',
    'Низкий': '🟢'
}

CATEGORIES = ['Учеба', 'Работа', 'Личное', 'Другое']

user_data = {}


# Функция регистрации пользователя

def register_user(user_id, first_name):
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            users = list(reader)
            if not any(user[0] == str(user_id) for user in users):
                with open(USERS_FILE, 'a', encoding='utf-8', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([user_id, first_name])
    except FileNotFoundError:
        with open(USERS_FILE, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([user_id, first_name])


# Функция для загрузки задач пользователя

def load_tasks_from_csv(user_id):
    tasks = []
    file_path = f'task_user_{user_id}.csv'
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                tasks.append({
                    'name': row['name'],
                    'description': row['description'],
                    'priority': row['priority'],
                    'category': row['category'],
                    'due_date': row['due_date'],
                    'reminder': row['reminder']
                })
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
    return tasks


# Функция для сохранения задачи в файл пользователя

def save_task_to_csv(task, user_id):
    file_path = f'task_user_{user_id}.csv'
    try:
        file_exists = os.path.exists(file_path)
        with open(file_path, 'a', newline='', encoding='utf-8') as file:
            fieldnames = ['name', 'description', 'priority', 'category', 'due_date', 'reminder']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(task)
    except Exception as e:
        print(f"Ошибка при записи задачи в файл: {e}")


# Функция для обновления задачи в файле пользователя

def update_task_in_csv(tasks, user_id):
    file_path = f'task_user_{user_id}.csv'
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file,
                                    fieldnames=['name', 'description', 'priority', 'category', 'due_date', 'reminder'])
            writer.writeheader()
            writer.writerows(tasks)
    except Exception as e:
        print(f"Ошибка при обновлении файла: {e}")


# Функция для запроса и добавления задач

def ask_for_task_details(message, step=0):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {}
    task = user_data[chat_id]

    if step == 0:
        bot.send_message(message.chat.id, "Введите название задачи:")
        bot.register_next_step_handler(message, ask_for_task_details, step=1)
    elif step == 1:
        task['name'] = message.text
        bot.send_message(message.chat.id, "Введите описание задачи:")
        bot.register_next_step_handler(message, ask_for_task_details, step=2)
    elif step == 2:
        task['description'] = message.text
        bot.send_message(message.chat.id, "Введите приоритет задачи (Высокий, Средний, Низкий):")
        bot.register_next_step_handler(message, ask_for_task_details, step=3)
    elif step == 3:
        priority = message.text
        if priority not in PRIORITY_EMOJIS:
            bot.send_message(message.chat.id, "Неверный приоритет! Пожалуйста, выберите из: Высокий, Средний, Низкий.")
            bot.register_next_step_handler(message, ask_for_task_details, step=3)
        else:
            task['priority'] = priority
            bot.send_message(message.chat.id, "Введите категорию задачи (Учеба, Работа, Личное, Другое):")
            bot.register_next_step_handler(message, ask_for_task_details, step=4)
    elif step == 4:
        category = message.text
        if category not in CATEGORIES:
            bot.send_message(message.chat.id, f"Неверная категория! Пожалуйста, выберите из: {', '.join(CATEGORIES)}.")
            bot.register_next_step_handler(message, ask_for_task_details, step=4)
        else:
            task['category'] = category
            bot.send_message(message.chat.id, "Введите дату выполнения задачи (формат: дд-мм-гггг):")
            bot.register_next_step_handler(message, ask_for_task_details, step=5)
    elif step == 5:
        due_date = message.text
        try:
            datetime.datetime.strptime(due_date, '%d-%m-%Y')
            task['due_date'] = due_date
            save_task_to_csv(task, chat_id)
            bot.send_message(message.chat.id, "Задача успешно добавлена!")
            del user_data[chat_id]
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат даты! Используйте формат: дд-мм-гггг.")
            bot.register_next_step_handler(message, ask_for_task_details, step=5)


# Обработчик команды /start

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.from_user.id, message.from_user.first_name)
    bot.reply_to(message, f'Привет, {message.from_user.first_name}! Я бот, который поможет тебе управлять задачами.')

    # Загружаем задачи пользователя
    tasks = load_tasks_from_csv(message.from_user.id)

    if not tasks:
        bot.send_message(message.chat.id,
                         "<b>У тебя нет задач!</b>\nДобавить новые можно с помощью команды <b>/add_task</b>.",
                         parse_mode="HTML")
    else:
        bot.send_message(message.chat.id,
                         f"<b>У тебя {len(tasks)} задач(и)!</b>\nПосмотреть их можно по команде <b>/task_list</b>.",
                         parse_mode="HTML")

    bot.send_message(message.chat.id, "Чтобы узнать все доступные команды и возможности бота, используй <b>/help</b>.",
                     parse_mode="HTML")


# Обработчик команды /task_list

@bot.message_handler(commands=['task_list'])
def task_list(message):
    tasks = load_tasks_from_csv(message.chat.id)
    if not tasks:
        bot.reply_to(message, "У тебя нет задач.")
        return

    response = "<b>Твои задачи:</b>\n\n"
    for task in tasks:
        emoji = PRIORITY_EMOJIS.get(task['priority'], '⚪')
        response += (
            f"<b>Название:</b> {task['name']}\n"
            f"<b>Описание:</b> {task['description']}\n"
            f"<b>Приоритет:</b> {emoji} {task['priority']}\n"
            f"<b>Категория:</b> {task['category']}\n"
            f"<b>Выполнить до:</b> {task['due_date']}\n\n"
        )
    bot.send_message(message.chat.id, response)


# Обработчик команды /help

@bot.message_handler(commands=['help'])
def help(message):
    help_text = """
    <b>Привет! Вот список доступных команд, которые ты можешь использовать:</b>

    <b>/start</b> - Начни работу с ботом. Приветственное сообщение и основная информация.

    <b>/task_list</b> - Получить список всех задач, которые у тебя есть.

    <b>/add_task</b> - Добавить новую задачу. Бот пошагово запросит у тебя все необходимые данные для создания задачи.

    <b>/delete_task</b> - Удалить задачу. Бот покажет список всех твоих задач, и ты сможешь выбрать, какую удалить.

    <b>/edit_task</b> - Редактировать задачу. Бот предложит выбрать задачу и изменить её название, описание, приоритет, дату выполнения или категорию.

    <b>/remind</b> - Установить напоминание для задачи. Ты можешь выбрать задачу и установить для неё напоминание на определённое время.

    <b>/help</b> - Показать это сообщение с описанием всех команд.

    <b>Подсказка:</b> Для каждой команды ты можешь следовать инструкциям, которые бот будет отправлять шаг за шагом.

    Если у тебя возникнут вопросы, не стесняйся обратиться!
    """
    bot.reply_to(message, help_text, parse_mode="HTML")


# Обработчик команды /add_task

@bot.message_handler(commands=['add_task'])
def add_task(message):
    bot.send_message(message.chat.id, "Начнем добавлять новую задачу. Следуйте инструкциям.")
    ask_for_task_details(message)


# Обработчик команды /delete_task с интерактивными кнопками

@bot.message_handler(commands=['delete_task'])
def delete_task(message):
    tasks = load_tasks_from_csv(message.chat.id)
    if not tasks:
        bot.reply_to(message, "У тебя нет задач.")
        return

    # Создаем клавиатуру с кнопками для каждой задачи

    markup = InlineKeyboardMarkup()
    for idx, task in enumerate(tasks, 1):
        button = InlineKeyboardButton(task['name'], callback_data=f"delete_{idx}")
        markup.add(button)

    bot.send_message(message.chat.id, "Выберите задачу для удаления:", reply_markup=markup)


# Обработчик нажатия на кнопку для удаления задачи

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def process_task_for_deletion(call):
    task_index = int(call.data.split('_')[1]) - 1  # Индекс задачи
    tasks = load_tasks_from_csv(call.message.chat.id)

    if task_index < 0 or task_index >= len(tasks):
        bot.send_message(call.message.chat.id, "Неверная задача.")
        return

    task = tasks.pop(task_index)  # Удаляем задачу из списка
    update_task_in_csv(tasks, call.message.chat.id)  # Обновляем CSV файл

    bot.send_message(call.message.chat.id, f"Задача '{task['name']}' была удалена.")


# Обработчик выбора задачи для удаления

def process_task_for_deletion(message, tasks):
    try:
        task_number = int(message.text)
        if task_number < 1 or task_number > len(tasks):
            bot.send_message(message.chat.id, "Неверный номер задачи. Попробуйте снова.")
            bot.register_next_step_handler(message, process_task_for_deletion, tasks)
        else:
            task = tasks.pop(task_number - 1)  # Удаляем задачу из списка
            update_task_in_csv(tasks, message.chat.id)  # Обновляем CSV файл
            bot.send_message(message.chat.id, f"Задача '{task['name']}' была удалена.")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный номер задачи.")
        bot.register_next_step_handler(message, process_task_for_deletion, tasks)


# Обработчик команды /edit_task с интерактивными кнопками

@bot.message_handler(commands=['edit_task'])
def edit_task(message):
    tasks = load_tasks_from_csv(message.chat.id)
    if not tasks:
        bot.reply_to(message, "У тебя нет задач.")
        return

    # Сначала выбираем задачу из списка

    markup = InlineKeyboardMarkup()
    for idx, task in enumerate(tasks, 1):
        markup.add(InlineKeyboardButton(task['name'], callback_data=f"choose_task_{idx}"))

    bot.send_message(message.chat.id, "Выберите задачу для редактирования:", reply_markup=markup)


# Обработчик для выбора задачи

@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_task_"))
def choose_task_for_editing(call):
    task_index = int(call.data.split('_')[2]) - 1  # Получаем индекс задачи
    tasks = load_tasks_from_csv(call.message.chat.id)

    if task_index < 0 or task_index >= len(tasks):
        bot.send_message(call.message.chat.id, "Неверная задача.")
        return

    task = tasks[task_index]

    # После выбора задачи предлагаем редактировать её поля

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Название", callback_data=f"edit_{task_index}_name"))
    markup.add(InlineKeyboardButton("Описание", callback_data=f"edit_{task_index}_description"))
    markup.add(InlineKeyboardButton("Приоритет", callback_data=f"edit_{task_index}_priority"))
    markup.add(InlineKeyboardButton("Дата выполнения", callback_data=f"edit_{task_index}_due_date"))
    markup.add(InlineKeyboardButton("Категория", callback_data=f"edit_{task_index}_category"))

    bot.send_message(call.message.chat.id, "Что вы хотите редактировать?", reply_markup=markup)


# Обработчик редактирования задачи

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def handle_task_edit_callback(call):
    bot.answer_callback_query(call.id)  # Подтверждаем callback

    # Корректное разбиение callback_data
    task_index = int(call.data.split('_')[1])
    action = '_'.join(call.data.split('_')[2:])  # Соединяем всё после второго элемента

    tasks = load_tasks_from_csv(call.message.chat.id)
    task = tasks[task_index]

    if action == "name":
        msg = bot.send_message(call.message.chat.id, "Введите новое название задачи:")
        bot.register_next_step_handler(msg, edit_task_name, task, tasks)
    elif action == "description":
        msg = bot.send_message(call.message.chat.id, "Введите новое описание задачи:")
        bot.register_next_step_handler(msg, edit_task_description, task, tasks)
    elif action == "priority":
        msg = bot.send_message(call.message.chat.id, "Введите новый приоритет задачи (Высокий, Средний, Низкий):")
        bot.register_next_step_handler(msg, edit_task_priority, task, tasks)
    elif action == "due_date":  # Исправлено
        msg = bot.send_message(call.message.chat.id, "Введите новую дату выполнения задачи (формат: дд-мм-гггг):")
        bot.register_next_step_handler(msg, edit_task_due_date, task, tasks)
    elif action == "category":
        msg = bot.send_message(call.message.chat.id, f"Выберите новую категорию задачи: {', '.join(CATEGORIES)}")
        bot.register_next_step_handler(msg, edit_task_category, task, tasks)

# Обработчики редактирования полей задачи

def edit_task_name(message, task, tasks):
    task['name'] = message.text
    bot.send_message(message.chat.id, f"Название задачи успешно изменено на: {task['name']}")
    update_task_in_csv(tasks, message.chat.id)
    bot.send_message(message.chat.id, "Задача обновлена!")

# Обработчик редактирования описания

def edit_task_description(message, task, tasks):
    task['description'] = message.text
    bot.send_message(message.chat.id, f"Описание задачи успешно изменено.")
    update_task_in_csv(tasks, message.chat.id)
    bot.send_message(message.chat.id, "Задача обновлена!")

# Обработчик редактирования категории

def edit_task_category(message, task, tasks):
    category = message.text
    if category not in CATEGORIES:
        bot.send_message(message.chat.id, f"Неверная категория! Пожалуйста, выберите из: {', '.join(CATEGORIES)}.")
        bot.register_next_step_handler(message, edit_task_category, task, tasks)
    else:
        task['category'] = category
        bot.send_message(message.chat.id, f"Категория задачи успешно изменена на: {task['category']}")
        update_task_in_csv(tasks, message.chat.id)
        bot.send_message(message.chat.id, "Задача обновлена!")

# Обработчик редактирования приоритета

def edit_task_priority(message, task, tasks):
    priority = message.text
    if priority not in PRIORITY_EMOJIS:
        bot.send_message(message.chat.id, "Неверный приоритет! Пожалуйста, выберите из: Высокий, Средний, Низкий.")
        bot.register_next_step_handler(message, edit_task_priority, task, tasks)
    else:
        task['priority'] = priority
        bot.send_message(message.chat.id, f"Приоритет задачи успешно изменен на: {task['priority']}")
        update_task_in_csv(tasks, message.chat.id)
        bot.send_message(message.chat.id, "Задача обновлена!")


# Обработчик редактирования даты

def edit_task_due_date(message, task, tasks):
    try:
        due_date = message.text
        datetime.datetime.strptime(due_date, '%d-%m-%Y')  # Проверка формата
        task['due_date'] = due_date
        bot.send_message(message.chat.id, f"Дата выполнения задачи успешно изменена на: {task['due_date']}")
        update_task_in_csv(tasks, message.chat.id)
        bot.send_message(message.chat.id, "Задача обновлена!")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат даты! Используйте формат: дд-мм-гггг.")
        bot.register_next_step_handler(message, edit_task_due_date, task, tasks)


# Обработчик команды /remind

@bot.message_handler(commands=['remind'])
def remind(message):
    tasks = load_tasks_from_csv(message.chat.id)
    if not tasks:
        bot.reply_to(message, "У тебя нет задач.")
        return

    response = "<b>Список задач для установки напоминания:</b>\n\n"
    for idx, task in enumerate(tasks, 1):
        response += f"{idx}. {task['name']}\n"

    bot.send_message(message.chat.id, response)
    bot.send_message(message.chat.id, "Введите номер задачи для которой хотите установить напоминание:")

    bot.register_next_step_handler(message, process_task_for_reminder, tasks)


# Обработчик выбора задачи для напоминания

def process_task_for_reminder(message, tasks):
    try:
        task_number = int(message.text)
        if task_number < 1 or task_number > len(tasks):
            bot.send_message(message.chat.id, "Неверный номер задачи. Попробуйте снова.")
            bot.register_next_step_handler(message, process_task_for_reminder, tasks)
        else:
            task = tasks[task_number - 1]
            bot.send_message(message.chat.id, f"Вы выбрали задачу: {task['name']}. Установим для нее напоминание.")

            bot.send_message(message.chat.id, "Введите дату и время напоминания (формат: дд-мм-гггг чч:мм):")
            bot.register_next_step_handler(message, process_reminder_time, task, tasks)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный номер задачи.")
        bot.register_next_step_handler(message, process_task_for_reminder, tasks)


# Обработчик ввода времени напоминания

def process_reminder_time(message, task, tasks):
    try:
        reminder_time = message.text
        reminder_datetime = datetime.datetime.strptime(reminder_time, '%d-%m-%Y %H:%M')
        task['reminder'] = reminder_datetime.strftime('%d-%m-%Y %H:%M')

        print(f"Установлено напоминание для задачи '{task['name']}' на {task['reminder']}")

        # Сохраняем обновленную задачу с напоминанием

        update_task_in_csv(tasks, message.chat.id)

        bot.send_message(message.chat.id,
                         f"Напоминание для задачи '{task['name']}' установлено на {reminder_datetime.strftime('%d-%m-%Y %H:%M')}.")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат времени! Пожалуйста, используйте формат: дд-мм-гггг чч:мм.")
        bot.register_next_step_handler(message, process_reminder_time, task, tasks)


# Функция для отправки напоминания с улучшенным оформлением

def send_reminder_for_task(task, user_id):
    print(f"Отправка напоминания пользователю {user_id} для задачи '{task['name']}'")

    emoji_priority = PRIORITY_EMOJIS.get(task['priority'], '⚪')  # Эмодзи для приоритета
    reminder_message = (
        f"<b>⏰ Напоминание!</b>\n\n"
        f"<b>Задача:</b> {task['name']}\n"
        f"<b>Описание:</b> {task['description']}\n\n"
        f"<b>Приоритет:</b> {emoji_priority} {task['priority']}\n"
        f"<b>Категория:</b> {task['category']}\n"
        f"<b>Выполнить до:</b> {task['due_date']}\n\n"
        f"<b>Не забудь выполнить задачу в срок!</b>"
    )

    bot.send_message(user_id, reminder_message, parse_mode='HTML')


# Функция для проверки напоминаний и их выполнения

def check_reminders():
    print("Проверка напоминаний...")
    users = {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                user_id = row[0]
                tasks = load_tasks_from_csv(user_id)
                users[user_id] = tasks
    except FileNotFoundError:
        print("Файл пользователей не найден.")

    # Проверяем задачи для каждого пользователя

    for user_id, tasks in users.items():
        for task in tasks:
            if task['reminder']:
                reminder_time = datetime.datetime.strptime(task['reminder'], '%d-%m-%Y %H:%M')
                if reminder_time <= datetime.datetime.now():
                    send_reminder_for_task(task, user_id)
                    task['reminder'] = ''  # очищаем напоминание
                    update_task_in_csv(tasks, user_id)


# Запуск проверки напоминаний для всех пользователей

def schedule_reminder_check():
    schedule.every(1).minute.do(check_reminders)

    while True:
        schedule.run_pending()
        time.sleep(1)


# Запуск бота

if __name__ == '__main__':
    schedule_thread = threading.Thread(target=schedule_reminder_check)
    schedule_thread.daemon = True
    schedule_thread.start()

    bot.polling(none_stop=True)