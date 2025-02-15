import sqlite3
import time
import random
import json
from enum import Enum

class SessionState(Enum):
    LOGIN = "login"
    MENU = "menu"
    ADD_NOTE = "add_note"
    NOTES_LIST = "notes_list"
    DEL_NOTE = "del_note"
    EDIT_NOTE = "edit_note"


class UserService:
    def __init__(self):
        self.db_name= "pet_notes_database.db"

    def init(self):  # нициализация таблички пользователей
        connection = sqlite3.connect(self.db_name)
        connection.cursor().execute("""CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER NOT NULL,
        username CHAR,
        created_at INTEGER,
        state CHAR NOT NULL,
        json_data CHAR
        );
        """)
        connection.commit()
        connection.close()

# ЗДЕСЬ БЫЛ check

    def add(self, user):  # tg_id,username,created_at,state,json_data
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("""INSERT INTO Users(
        tg_id,username,state,json_data, created_at)
        VALUES(?, ?, ?, ?, ?)  
        """, user.to_model()[:-1]) # срезаем user_id, спецом пихнули его в конец
        connection.commit()
        connection.close()


    def get(self,tg_id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("SELECT tg_id, username, state, json_data, created_at, user_id FROM Users WHERE tg_id = ? LIMIT 1", (tg_id,))
        result = cursor.fetchall()
        connection.close()
        if result:
            return UserDto.from_model(result[0])
        else:
            new_user = UserDto(tg_id, 'tg_username', state="start")
            self.add(new_user)  # Метод add внутри UserService принимает объект UserDto
            return self.get(tg_id)


    def update(self,user): # state + json
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("UPDATE Users SET tg_id = ?, username = ?, state = ?, json_data = ?, created_at = ? WHERE user_id=?", user.to_model())
        connection.commit()
        connection.close()


class UserDto:
    def __init__(self, tg_id,username,state="start",json_data=None, created_at = None, user_id = None):
        self.tg_id = tg_id
        self.username = username
        if created_at == None:
            created_at = round(time.time())
        self.created_at = created_at
        self.state = state
        self.json_data = json_data
        self.user_id = user_id


    def to_model(self): #для работы с бд для запроса эскуль
        return (self.tg_id, self.username, self.state, self.json_data, self.created_at, self.user_id)

    @staticmethod
    def from_model(row): #принимает то что из базы ряд и возвращает дтошку
        return UserDto(row[0],row[1],row[2],row[3],row[4],row[5])


class NoteService:
    def __init__(self):
        self.db_name = "pet_notes_database.db"
        
    def init_data(self):
        connection = sqlite3.connect(self.db_name)
        connection.cursor().execute("""
CREATE TABLE IF NOT EXISTS Notes (
    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title CHAR(200),
    content CHAR(4500),
    created_at INTEGER NOT NULL,
    updated_at INTEGER,
    is_deleted INTEGER,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE RESTRICT
);
        """) #note_id CHAR
        connection.commit()
        connection.close()

        
    def add(self, note_dto):
        connection = sqlite3.connect(self.db_name)
        connection.cursor().execute("""
INSERT INTO Notes(user_id,title,content,created_at, updated_at)
VALUES(?, ?, ?, ?, ?)
        """, note_dto.to_model()[:-1])
        connection.commit()
        connection.close()
        
    def get_all(self, user_id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                user_id, 
                title, 
                content,
                created_at,
                updated_at,
                note_id
            FROM 
                Notes 
            WHERE 
                (is_deleted IS NULL OR is_deleted = 0)
                AND user_id = ?""", (user_id,))
        data = cursor.fetchall()
        connection.close()
                
        result = []
        for row in data:
            result.append(NoteDto.from_model(row))
            
        return result
        
    def delete_func(self, note_id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute('UPDATE Notes SET is_deleted = 1 WHERE note_id=?',(note_id,))
        connection.commit()
        connection.close()
        
    def update(self, note):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute('UPDATE Notes set user_id = ?, title = ?, content = ?, created_at = ?, updated_at =? WHERE note_id =?', note.to_model())
        connection.commit()
        connection.close()


    def get_note(self, note_id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute('SELECT user_id, title, content, created_at, updated_at, note_id from Notes WHERE note_id=?', (note_id,))
        data = cursor.fetchall()
        row = data[0]
        print(row[2])
        note = NoteDto.from_model(row)
        connection.close()
        return note

class NoteDto:
    def __init__(self, user_id, title, content, created_at = None, updated_at = None, note_id = None):
        self.note_id = note_id
        self.user_id = user_id
        self.title = title
        self.content = content
        if created_at == None:
            created_at = round(time.time())
        self.created_at = created_at
        if updated_at == created_at:
            updated_at = round(time.time())
        self.updated_at = updated_at
        
    def to_model(self): #для работы с бд для запроса эскуль
        return (self.user_id, self.title, self.content, self.created_at, self.updated_at, self.note_id)

    @staticmethod
    def from_model(row): #принимает шо высрала база
        return NoteDto(row[0], row[1], row[2], row[3], row[4],row[5])

        
    def print(self):
        print(f"{self.note_id} ({self.title}): {self.content}")

        




    
class Menu:
    def __init__(self, need_init = False):
        self.note_service = NoteService()
        self.user_service = UserService()
        
        if need_init:
            self.note_service.init_data()
            self.user_service.init() #инициализируем табличку с юзерами
            
        self.tg_id = self.login()
        self.user = self.user_service.get(self.tg_id) # dto object of User
        self.user_id = UserDto.to_model(self.user)[-1]

        state = SessionState.LOGIN.value
        self.user.state = state
        self.user_service.update(self.user)  # апдейтим стейт

        
    def login(self):
        while True:
            print("Введите свой telegram id\n Либо 111, либо 222, либо 333")
            tg_id = input()
            if tg_id.isnumeric() and int(tg_id) in (111, 222, 333):
                return tg_id
            
            print("tg_id должно быть числом и равняться 111/222/333")





    def start(self):
        while True:
            user = self.user_service.get(self.tg_id)  # раскатываем дто объект юзера обязательно заново
            state = SessionState.MENU.value
            user.state = state
            self.user_service.update(user)  # апдейтим стейт

            print("Заметки\n1.Добавить\n2.Мои заметки\n3.Тыкалка\n4.Удалить заметки\n5.Редактировать заметки\n6.Выход")
            command = input("Plz write 1-3: ")
            if command == "1":
                self.add()
            elif command == "2":
                self.show_all()
            elif command =="3":
                self.tikalka()
            elif command=="4":
                self.delete()
            elif command=="5":
                self.edit()
            elif command=="6":
                print("Поки споки")
                exit()
            else:
                print("Неверная команда!")


    def edit(self):
        print('Выберите заметку для редактирования: ')
        self.show_all()

        user = self.user_service.get(self.tg_id)  # раскатываем дто объект юзера обязательно заново
        state = SessionState.EDIT_NOTE.value
        user.state = state
        self.user_service.update(user)  # апдейтим стейт

        index = input("Введи note_id заметки (первый столбец таблицы):")
        json_data = json.dumps({"edit_index": index}, ensure_ascii=False)
        user.json_data = json_data
        self.user_service.update(user)  # апдейтим json

        note = self.note_service.get_note(index)

        content = input("Редактирование заметки: ")
        note.content = content
        json_data = json.dumps({"edit_content": content}, ensure_ascii=False)
        user.json_data = json_data
        self.user_service.update(user)  # апдейтим json
        self.note_service.update(note)
        print("Заметка обновлена!")

        json_data = json.dumps({"edit_done": content}, ensure_ascii=False)
        user.json_data = json_data
        self.user_service.update(user)  # апдейтим json
        return

    def delete(self):
        print("Выбери заметку, которую хочешь удалить!")
        self.show_all()

        user = self.user_service.get(self.tg_id)  # раскатываем дто объект юзера обязательно заново
        state = SessionState.DEL_NOTE.value
        user.state = state
        self.user_service.update(user)  # апдейтим стейт

        index = input("Введи note_id заметки (первый столбец таблицы):")
        json_data = json.dumps({"del_index": index}, ensure_ascii=False)
        user.json_data = json_data
        self.user_service.update(user)  # апдейтим json

        question = input("Вы действительно хотите удалить заметку?")
        self.note_service.delete_func(index)
        json_data = json.dumps({"del_done": index}, ensure_ascii=False)
        user.json_data = json_data
        self.user_service.update(user)  # апдейтим json

        print("Заметка удалена")
        return


                
    def add(self):

        user = self.user_service.get(self.tg_id) #раскатываем дто объект юзера обязательно заново
        state = SessionState.ADD_NOTE.value
        user.state = state
        self.user_service.update(user) #апдейтим стейт

        title = input("Введите название заметки\n")
        json_data = json.dumps({"add_title":title}, ensure_ascii=False)
        user.json_data = json_data
        self.user_service.update(user) #апдейтим json

        content = input("Введите текст\n")
        json_data = json.dumps({"add_content": content}, ensure_ascii=False)
        user.json_data = json_data
        self.user_service.update(user)  # апдейтим json

        note = NoteDto(self.user_id, title, content)
        self.note_service.add(note)
        #print(note.user_id)
        print("Заметка создана")

        json_data = json.dumps({"add_done": content}, ensure_ascii=False)
        user.json_data = json_data
        self.user_service.update(user)  # апдейтим json
        return
        
    def show_all(self):
        notes = self.note_service.get_all(self.user_id)

        user = self.user_service.get(self.tg_id)  # раскатываем дто объект юзера обязательно заново
        state = SessionState.NOTES_LIST.value
        user.state = state
        self.user_service.update(user)  # апдейтим стейт

        print("=====[ Заметки ]=====")
        for note in notes:
            note.print()
        print()

    def tikalka(self):
        print("Случайное число от 1 до 100:", random.randint(1, 100),"\nВызываю снова меню","\n--------------")
        return
                
def main():
    menu = Menu(True)
    menu.start()
    
    
main()