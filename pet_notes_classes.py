import sqlite3
import random
import time
import pandas as pd
import random

class NoteService:
    def __init__(self):
        self.db_name = "pet_notes_database2.db"
        
    def init_data(self):
        connection = sqlite3.connect(self.db_name)
        connection.cursor().execute("""
CREATE TABLE IF NOT EXISTS Notes (
    id INTEGER,
    username CHAR(40) NOT NULL,
    title CHAR(40),
    content CHAR(1000),
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
        """, (note_dto.user_id, 'test', note_dto.name, note_dto.content, note_id, round(time.time())))
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
        
    def delete_func(self, id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute('UPDATE Notes SET is_deleted = 1 WHERE note_id=?',(id,))
        connection.commit()
        connection.close()
        
    def update(self, note):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute('UPDATE Notes set content = ?,updated_at =? WHERE note_id =?', note.to_model())
        connection.commit()
        connection.close()


    def get_note(self, id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute('SELECT title, content, note_id from Notes WHERE note_id=?', (id,))
        data = cursor.fetchall()
        row = data[0]
        print(row)
        note = note_from_model(row)
        connection.close()
        return note

class NoteDto:
    def __init__(self, user_id, name, content, id = None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.content = content
        
    def to_model(self):
        updated_at = round(time.time())
        return (self.content, updated_at, self.id)

    def to_content(self):
        return (self.content)
        
    def print(self):
        print(f"{self.id} ({self.name}): {self.content}")

        
        
def note_from_model(row):
    return NoteDto(None, row[0], row[1], row[2])


    
class Menu:
    def __init__(self, need_init = False):
        self.note_service = NoteService()
        
        if (need_init):
            self.note_service.init_data()
            
        self.id = self.login()
        
    def login(self):
        while True:
            print("Введите свой id")
            id = input()
            if id.isnumeric():
                return id
            
            print("id должно быть числом")

            
            
    def start(self):
        while True:
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
        index = input("Введи note_id заметки (первый столбец таблицы):")
        note = self.note_service.get_note(index)
        print(note.content)
        content = input("Редактирование заметки: ")
        note.content = content
        self.note_service.update(note)
        print("Заметка обновлена!")
        return

    def delete(self):
        print("Выбери заметку, которую хочешь удалить!")
        self.show_all()
        index = input("Введи note_id заметки (первый столбец таблицы):")
        self.note_service.delete_func(index)
        print("Заметка удалена")
        return


                
    def add(self):
        name = input("Введите название заметки\n")
        content = input("Введите текст\n")
        note = NoteDto(self.id, name, content)
        self.note_service.add_note(note)
        print("Заметка создана")
        return
        
    def show_all(self):
        notes = self.note_service.get_all(self.id)
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