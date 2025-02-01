import sqlite3
import random
import time
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton #юзаем реплай клаву
from aiogram.filters import CommandStart,Command
from aiogram.types import FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext


class NoteService:
    def __init__(self):
        self.db_name = "pet_notes_telegram_database.db"

    def init_data(self):
        connection = sqlite3.connect(self.db_name)
        connection.cursor().execute("""
CREATE TABLE IF NOT EXISTS Notes (
    id INTEGER,
    username CHAR,
    title CHAR(40),
    content CHAR(4500),
    created_at INTEGER NOT NULL,
    updated_at INTEGER,
    is_deleted INTEGER,
    note_id CHAR
);
        """)
        connection.commit()
        connection.close()


    def __get_max_id(self, user_id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(1) FROM Notes WHERE id = ?", (user_id,))
        result = cursor.fetchall()
        connection.close()
        return result[0][0]


    def add_note(self, note_dto):
        note_id = f"{note_dto.user_id}_{self.__get_max_id(note_dto.user_id)}"
        connection = sqlite3.connect(self.db_name)
        connection.cursor().execute("""
INSERT INTO Notes(id,username,title,content,note_id, created_at)
VALUES(?, ?, ?, ?, ?, ?)
        """, (note_dto.user_id, note_dto.username, note_dto.name, note_dto.content, note_id, round(time.time())))
        connection.commit()
        connection.close()


    def get_all(self, user_id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                title, 
                content,
                note_id
            FROM 
                Notes 
            WHERE 
                (is_deleted IS NULL OR is_deleted = 0)
                AND id = ?""", (user_id,))
        data = cursor.fetchall()
        connection.close()
        result = []
        for row in data:
            result.append(note_from_model(row))
        return result

    def delete_func(self, note_id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute('UPDATE Notes SET is_deleted = 1 WHERE note_id=?', (note_id,))
        connection.commit()
        connection.close()

def note_from_model(row):
    return NoteDto(user_id=None, name=row[0], content=row[1], note_id=row[2])

class NoteDto:
    def __init__(self, user_id, name, content, username=None, note_id=None):
        self.username = username
        self.user_id = user_id
        self.name = name
        self.content = content
        self.note_id = note_id

    def to_model(self):
        updated_at = round(time.time())
        return (self.content, updated_at, self.id)

    def to_content(self):
        return (self.content)

    def print(self):
        print(f"{self.id} ({self.name}): {self.content}")

class AddNote(StatesGroup): #конструктор добавления заметок
    name = State()
    content = State()

class DelNote(StatesGroup): #конструктор удаления заметок
    note_id = State()


class TelegramBot:

    def __init__(self, token, need_init = False):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.logged_users = {}
        self.note_service = NoteService()

        #if (need_init):
        self.note_service.init_data()

    async def login(self, message: Message):
        """Логин пользователя"""
        user = message.from_user
        user_data = {
            "telegram_id": user.id,
            "full_name": user.full_name,
            "username": user.username,
            "language_code": user.language_code,
            "is_bot": user.is_bot
        }
        self.logged_users[user.id] = user_data
        self.id = user.id
        self.username = user.username
        await message.answer("Успешная авторизация!")

    async def show_all(self,user_id):
        notes = self.note_service.get_all(user_id)
        if not notes:
            await message.answer("У вас нет заметок.")
        else:
            result = "=====[ Заметки ]=====\n"
            for note in notes:
                result += f"Заголовок: {note.name}\nКонтент:{note.content}\nID заметки: {note.note_id}\n\n"
            return result



    def setup_handlers(self):
        keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Добавить"),
                                                  KeyboardButton(text="Мои заметки")],
                                                  [KeyboardButton(text="Удалить заметку"),
                                                  KeyboardButton(text="Редактировать заметку")]],
                                       resize_keyboard=True,
                                       input_field_placeholder="Выберите пункт меню...")
        """Настройка обработчиков"""
        @self.dp.message(CommandStart())
        async def start_command(message: Message):
            await self.login(message)
            await message.answer(f"Привет, {message.from_user.first_name}. Твой TG ID: {message.from_user.id}. Готов помочь с твоими заметками! ", reply_markup=keyboard)

        @self.dp.message(F.text == "Добавить")
        async def add_one(message: Message, state: FSMContext):
            await state.set_state(AddNote.name)  # шаг 1 input имени заметки
            await message.answer("Введите заголовок заметки:")

        @self.dp.message(AddNote.name)  # ловим что юзер вводит имя
        async def add_two(message: Message, state: FSMContext):
            await state.update_data(name=message.text)  # сохраняем в кэше
            await state.set_state(AddNote.content)  # след. шан input контента
            await message.answer("Введите вашу заметку:")

        @self.dp.message(AddNote.content)  # ловим что юзер вводит content
        async def two_three(message: Message, state: FSMContext):
            await state.update_data(content=message.text)  # сохраняем в кэше
            data = await state.get_data()  # достаём информацию и можно отправить в базу данных
            name = data["name"]
            content = data["content"]
            note = NoteDto(self.id, name, content,self.username)
            self.note_service.add_note(note)
            await message.answer("Заметка добавлена!")
            await message.answer(f"Заголовок: {data['name']} \nКонтент: {data['content']}", reply_markup=keyboard)
            await state.clear()

        @self.dp.message(F.text == "Мои заметки")
        async def show(message: Message):
            await message.answer(await self.show_all(message.from_user.id), reply_markup=keyboard) # мы это делаем потому, что если использовать self.id получается баг

        @self.dp.message(F.text == "Удалить заметку")
        async def del_nts(message: Message, state: FSMContext):
            await message.answer(await self.show_all(message.from_user.id))
            await state.set_state(DelNote.note_id)
            await message.answer("Введите ID заметки, которую хотите удалить")

        @self.dp.message(DelNote.note_id)  # ловим что юзер вводит note_id
        async def del_two(message: Message, state: FSMContext):
            await state.update_data(note_id=message.text)  # сохраняем в кэше note_id
            data = await state.get_data()
            note_id = data["note_id"]
            self.note_service.delete_func(note_id)
            await message.answer("Заметка удалена!", reply_markup=keyboard)
            await state.clear()









        @self.dp.message(F.text == "Проверка")
        async def cmd_table(message: Message):
            user_id = message.from_user.id
            if user_id in self.logged_users:
                user_data = self.logged_users[user_id]
                await message.answer(
                    f"Привет, {user_data['full_name']}!\n"
                    f"Ваш Telegram ID: {user_data['telegram_id']}\n"
                    f"Ваш Username: @{user_data['username']}\n"
                    f"Язык интерфейса: {user_data['language_code']}\n"
                    f"Вы бот? {'Да' if user_data['is_bot'] else 'Нет'}"
                )
            else:
                await message.answer("Вы еще не залогинились. Введите /start.")

    async def run(self):
        """Запуск бота"""
        self.setup_handlers()
        await self.dp.start_polling(self.bot)


if __name__ == "__main__":
    TOKEN = "7986753325:AAH4NqYDGe_GGt-srvUq4C_w9CofE2yah0k"
    bot = TelegramBot(TOKEN)
    asyncio.run(bot.run())


