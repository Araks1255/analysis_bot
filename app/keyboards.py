from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Анализ трат")],
        [KeyboardButton(text="Более подробная информация")]
    ],
    resize_keyboard=True
)

yes = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да")]
    ],
    resize_keyboard=True
)

cancel = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Отмена")]
    ],
    resize_keyboard=True
)