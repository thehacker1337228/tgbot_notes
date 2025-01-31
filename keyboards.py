from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

#Инлайн клава (встроенная) - отправляет коллбэки
#Реплай клава отправляет сообщения

main = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton(text="Каталог", callback_data="catalog")],
    [InlineKeyboardButton(text="Корзина", callback_data="basket"),
     InlineKeyboardButton(text="Контактi",callback_data="contacts")]
])


settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="YouTube", url="https://youtube.com")]
])

cars = ["Lada","Zaz","Uazik"]

async def inline_cars():
    keyboard = InlineKeyboardBuilder()
    for car in cars:
        keyboard.add(InlineKeyboardButton(text=car, url="https://avito.ru/"))
    return keyboard.adjust(2).as_markup()