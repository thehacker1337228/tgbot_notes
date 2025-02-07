import sqlite3
import time
import random
import json
from enum import Enum

class SessionState(Enum):
    LOGIN = 1
    MENU = 2
    ADD_NOTE = 3
    NOTES_LIST = 4
    DEL_NOTE = 5
    EDIT_NOTE = 6


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

    def check(self, tg_id):
        try: #try except потому что если база файл с базой не создан, то швыряет ошибку sql поле не найдено
            connection = sqlite3.connect(self.db_name)
            cursor = connection.cursor()
            cursor.execute("""SELECT CASE 
            WHEN COUNT(1) > 0 THEN True ELSE False 
           END AS exists_state FROM Users WHERE tg_id = ?;""", (tg_id,))
            result = cursor.fetchall()
            connection.close()
            return result[0][0]  # 1 -true, 0-false
        except:
            return 0

    def add(self, user_dto):  # tg_id,username,created_at,state,json_data
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("""INSERT INTO Users(
        tg_id,username,created_at,state,json_data)
        VALUES(?, ?, ?, ?, ?)  
        """, user_dto)
        connection.commit()
        connection.close()


    def get(self,tg_id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM Users WHERE tg_id = ? LIMIT 1", (tg_id,))
        result = cursor.fetchall()
        connection.close()
        if self.check(tg_id)==1:
            return result[0][0]
        else:
            user = UserDto(tg_id,'tg_username',round(time.time()))
            user_object = user.user_dto()
            self.add(user_object)

    def state(self,state_num,user_id):
        state = SessionState(state_num).name
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("UPDATE Users SET state = ? WHERE user_id=?", (state,user_id))
        connection.commit()
        connection.close()

    def user_json(self,step,item,user_id):
        json_dict = {step:item}
        json_string = json.dumps(json_dict)
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("UPDATE Users SET json_data = ? WHERE user_id=?", (json_string,user_id))
        connection.commit()
        connection.close()

class UserDto:
    def __init__(self, tg_id,username,created_at,state="start",json_data=None):
        self.tg_id = tg_id
        self.username = username
        self.created_at = created_at
        self.state = state
        self.json_data = json_data

    def user_dto(self):
        return (self.tg_id, self.username, self.created_at, self.state, self.json_data)


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
        #note_id = f"{note_dto.user_id}_{self.__get_max_id(note_dto.user_id)}"
        connection = sqlite3.connect(self.db_name)
        connection.cursor().execute("""
INSERT INTO Notes(user_id,title,content, created_at)
VALUES(?, ?, ?, ?)
        """, (note_dto.user_id, note_dto.title, note_dto.content, round(time.time())))
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
                AND user_id = ?""", (user_id,))
        data = cursor.fetchall()
        connection.close()
                
        result = []
        for row in data:
            result.append(note_from_model(row))
            
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
        cursor.execute('UPDATE Notes set content = ?,updated_at =? WHERE note_id =?', note.to_model())
        connection.commit()
        connection.close()


    def get_note(self, note_id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute('SELECT title, content, note_id from Notes WHERE note_id=?', (note_id,))
        data = cursor.fetchall()
        row = data[0]
        print(row)
        note = note_from_model(row)
        connection.close()
        return note

class NoteDto:
    def __init__(self, user_id, title, content, note_id = None):
        self.note_id = note_id
        self.user_id = user_id
        self.title = title
        self.content = content
        
    def to_model(self):
        updated_at = round(time.time())
        return (self.content, updated_at, self.note_id)

    def to_content(self):
        return (self.content)
        
    def print(self):
        print(f"{self.note_id} ({self.title}): {self.content}")

        
        
def note_from_model(row):
    return NoteDto(None, row[0], row[1], row[2])


    
class Menu:
    def __init__(self, need_init = False):
        self.note_service = NoteService()
        self.user_service = UserService()
        
        if (need_init):
            self.note_service.init_data()
            self.user_service.init() #инициализируем табличку с юзерами
            
        self.tg_id = self.login()
        self.user_id = self.user_service.get(self.tg_id)
        self.state = self.user_service.state(1, self.user_id)
        
    def login(self):
        while True:
            print("Введите свой telegram id\n Либо 111, либо 222, либо 333")
            tg_id = input()
            if tg_id.isnumeric() and int(tg_id) in (111, 222, 333):
                return tg_id
            
            print("tg_id должно быть числом и равняться 111/222/333")




            
            
    def start(self):
        while True:
            self.user_service.state(2, self.user_id)
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
        self.user_service.state(6, self.user_id)
        index = input("Введи note_id заметки (первый столбец таблицы):")
        self.user_service.user_json("edit_index", index, self.user_id)
        note = self.note_service.get_note(index)
        content = input("Редактирование заметки: ")
        note.content = content
        self.user_service.user_json("edit_content", content, self.user_id)
        self.note_service.update(note)
        print("Заметка обновлена!")
        self.user_service.user_json("edit_done", content, self.user_id)
        return

    def delete(self):
        print("Выбери заметку, которую хочешь удалить!")
        self.show_all()
        self.user_service.state(5, self.user_id)
        index = input("Введи note_id заметки (первый столбец таблицы):")
        self.user_service.user_json("del_index", index, self.user_id)
        question = input("Вы действительно хотите удалить заметку?")
        self.note_service.delete_func(index)
        self.user_service.user_json("del_done", index, self.user_id)
        print("Заметка удалена")
        return


                
    def add(self):
        self.user_service.state(3, self.user_id)
        title = input("Введите название заметки\n")
        self.user_service.user_json("add_title",title,self.user_id)
        content = input("Введите текст\n")
        self.user_service.user_json("add_content",content,self.user_id)
        note = NoteDto(self.user_id, title, content)
        self.note_service.add(note)
        print("Заметка создана")
        self.user_service.user_json("add_done", content, self.user_id)
        return
        
    def show_all(self):
        notes = self.note_service.get_all(self.user_id)
        self.user_service.state(4, self.user_id)
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