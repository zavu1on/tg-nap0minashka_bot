from telebot import TeleBot
from telebot.types import Message, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dataclasses import dataclass
from datetime import datetime, timedelta
from _thread import start_new_thread
from time import time, sleep
from config import TOKEN

bot = TeleBot(TOKEN)
bot.set_my_commands([
    BotCommand('start', 'Запустить бота'),
    BotCommand('browse_tasks', 'Посмотреть запланированные задачи'),
    BotCommand('add_task', 'Запланировать задачу'),
    BotCommand('server_time', 'Получить время на сервере'),
    BotCommand('help', 'Помощь по командам')
])


@dataclass
class Task:
    id: int
    user_id: int
    notify_time: datetime = None
    text: str = None
    audio_path: str = None
    is_created: bool = False


tasks: list[Task] = []


@bot.message_handler(commands=['start'])
def start(message: Message):
    text = f'''
    Привет, <b>{message.chat.first_name}</b> 👋
    
Этот бот создан, чтобы напоминать о твоих важных делах 📍
    '''
    bot.send_message(message.chat.id, text, 'html')

    text = f'''
Введите /add_task , чтобы запланировать задачу ➕
Введите /browse_tasks , посмотреть запланированные задачи 📃
Введите /server_time , узнать время на сервере и вычислить разницу часовых поясов
    '''.strip()
    bot.send_message(message.chat.id, text, 'html')


@bot.message_handler(commands=['help'])
def help_(message: Message):
    text = f'''
Введите /add_task , чтобы запланировать задачу ➕
Введите /browse_tasks , посмотреть запланированные задачи 📃
Введите /server_time , узнать время на сервере и вычислить разницу часовых поясов
    '''.strip()
    bot.send_message(message.chat.id, text, 'html')


@bot.message_handler(commands=['server_time'])
def server_time(message: Message):
    bot.send_message(message.chat.id, str(datetime.now()))


@bot.message_handler(commands=['browse_tasks'])
def browse_tasks(message: Message):
    tasks_qs = list(filter(lambda t: t.user_id == message.chat.id, tasks))

    if not tasks_qs:
        bot.send_message(message.chat.id, 'Пока задач не наблюдаю 😪')

    for task in tasks_qs:
        if task.text:
            text = f'<b>{task.text}</b>\nНапомню: <i>{task.notify_time}</i>'
        else:
            text = f'<b>Аудио сообщение</b>\nНапомню: <i>{task.notify_time}</i>'

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Удалить 🗑️', callback_data=f'del-{task.id}'))

        bot.send_message(message.chat.id, text, 'html', reply_markup=markup)


@bot.message_handler(commands=['add_task'])
def add_task(message: Message):
    new_message = bot.send_message(message.chat.id, 'Напишите вашу задачу 🖊️ или запишиите голосовое сообщение 🎤')

    bot.register_next_step_handler(new_message, add_task_1_next_step_handler)


def add_task_1_next_step_handler(message: Message):
    if message.text:
        tasks.append(Task(
            int(time()),
            message.chat.id,
            text=message.text
        ))
    elif message.voice:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        path = f'./voice/{message.chat.id}_{int(time())}.ogg'

        with open(path, 'wb') as new_file:
            new_file.write(downloaded_file)

        tasks.append(Task(
            int(time()),
            message.chat.id,
            audio_path=path
        ))
    else:
        tasks.append(Task(
            message.chat.id,
            text='Пусто, блин :('
        ))

    text = '''
Теперь выберем время 🕑
Когда напомнить о твоем деле?

Введи время в формате <b>HH:MM:SS</b> ⌛
Или дату в формате <b>YYYY-MM-DD=HH:MM:SS</b> 📅
Или воспользуйся быстрыми кнопками для выбора времени 😁
    '''
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Через 15 минут', callback_data='fast-15min'))
    markup.add(InlineKeyboardButton('Через 30 минут', callback_data='fast-30min'))
    markup.add(InlineKeyboardButton('Через 1 час', callback_data='fast-1h'))
    markup.add(InlineKeyboardButton('Через 2 часа', callback_data='fast-2h'))
    markup.add(InlineKeyboardButton('Через 1 день', callback_data='fast-1d'))
    markup.add(InlineKeyboardButton('Через 2 дня', callback_data='fast-2d'))
    markup.add(InlineKeyboardButton('Через 1 неделю', callback_data='fast-1w'))

    new_message = bot.send_message(message.chat.id, text, 'html', reply_markup=markup)

    bot.register_next_step_handler(new_message, add_task_2_next_step_handler)


def add_task_2_next_step_handler(message: Message):
    if len(message.text) == 8:
        local_tasks = list(filter(lambda t: t.user_id == message.chat.id and not t.is_created, tasks))

        if not local_tasks:
            return bot.send_message(message.chat.id, 'Упс, что-то пошло не так\nНе получилось добавить таску, '
                                                     'попробуй заного 😥')

        task: Task = local_tasks[0]

        try:
            hours, minutes, seconds = list(map(int, message.text.split(':')))

            task.notify_time = datetime(
                datetime.now().year,
                datetime.now().month,
                datetime.now().day,
                hours,
                minutes,
                seconds,
                0,
            )

            task.is_created = True

            return bot.send_message(message.chat.id, 'Все прошло успешно!')
        except:
            pass

    elif len(message.text) == 19:
        local_tasks = list(filter(lambda t: t.user_id == message.chat.id and not t.is_created, tasks))

        if not local_tasks:
            return bot.send_message(message.chat.id, 'Упс, что-то пошло не так\nНе получилось добавить таску, '
                                                     'попробуй заного 😥')

        task: Task = local_tasks[0]

        try:
            years, months, days = list(map(int, message.text.split('=')[0].split('-')))
            hours, minutes, seconds = list(map(int, message.text.split('=')[1].split(':')))

            task.notify_time = datetime(
                years,
                months,
                days,
                hours,
                minutes,
                seconds,
                0,
            )

            task.is_created = True

            return bot.send_message(message.chat.id, 'Все прошло успешно!')
        except:
            pass

    bot.send_message(message.chat.id, 'Не получилось распознать время, давай попробуем еще раз 😥')

    text = '''
Выбери время 🕑
Когда напомнить о твоем деле?

Введи время в формате <b>HH:MM:SS</b> ⌛
Или дату в формате <b>YYYY-MM-DD-HH:MM:SS</b> 📅
Или воспользуйся быстрыми кнопками для выбора времени 😁
        '''
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Через 15 минут', callback_data='fast-15min'))
    markup.add(InlineKeyboardButton('Через 30 минут', callback_data='fast-30min'))
    markup.add(InlineKeyboardButton('Через 1 час', callback_data='fast-1h'))
    markup.add(InlineKeyboardButton('Через 2 часа', callback_data='fast-2h'))
    markup.add(InlineKeyboardButton('Через 1 день', callback_data='fast-1d'))
    markup.add(InlineKeyboardButton('Через 2 дня', callback_data='fast-2d'))
    markup.add(InlineKeyboardButton('Через 1 неделю', callback_data='fast-1w'))

    new_message = bot.send_message(message.chat.id, text, 'html', reply_markup=markup)

    bot.register_next_step_handler(new_message, add_task_2_next_step_handler)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call: CallbackQuery):
    if call.data:
        if call.data.startswith('del-'):
            task = list(filter(lambda t: t.id == int(call.data.split('-')[1]), tasks))

            if task:
                tasks.remove(task[0])
                bot.send_message(call.message.chat.id, 'Таска успешно удалилась!')
            else:
                bot.send_message(call.message.chat.id, 'Не удалось удалить задачку :(')
        elif call.data.startswith('fast-'):
            time_case = call.data.split('-')[1]
            message = call.message
            local_tasks = list(filter(lambda t: t.user_id == message.chat.id and not t.is_created, tasks))

            if not local_tasks:
                return bot.send_message(message.chat.id, 'Упс, что-то пошло не так\nНе получилось добавить таску, '
                                                         'попробуй заного 😥')

            task: Task = local_tasks[0]

            if time_case == '15min':
                task.notify_time = datetime.now() + timedelta(minutes=15)
            elif time_case == '30min':
                task.notify_time = datetime.now() + timedelta(minutes=30)
            elif time_case == '1h':
                task.notify_time = datetime.now() + timedelta(hours=1)
            elif time_case == '2h':
                task.notify_time = datetime.now() + timedelta(hours=2)
            elif time_case == '1d':
                task.notify_time = datetime.now() + timedelta(days=1)
            elif time_case == '2d':
                task.notify_time = datetime.now() + timedelta(days=2)
            elif time_case == '1w':
                task.notify_time = datetime.now() + timedelta(weeks=1)

            task.is_created = True
            bot.send_message(message.chat.id, 'Все прошло успешно!')

            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)


def notify_thread():
    while True:
        for task in tasks:
            if not task.notify_time:
                continue

            if task.notify_time.date() == datetime.now().date():
                if task.notify_time.time().hour == datetime.now().hour and \
                        task.notify_time.time().minute == datetime.now().minute:
                    if task.text:
                        bot.send_message(task.user_id, f'Напоминаю, что\n<b>{task.text}</b>')
                    else:
                        bot.send_message(task.user_id, 'Напоминаю, что...')
                        bot.send_voice(task.user_id, task.audio_path)

                    tasks.remove(task)

        sleep(1)


if __name__ == '__main__':
    print('BOT STARTED')
    start_new_thread(notify_thread, tuple(), {})
    bot.polling(True)
