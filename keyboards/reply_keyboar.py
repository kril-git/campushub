from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

r_kb_cancel = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Отмена")]
], resize_keyboard=True, one_time_keyboard=True)

r_kb_accounting = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Просмотр"),
     KeyboardButton(text="Поиск"),
     KeyboardButton(text="Добавить")],
    [KeyboardButton(text="Удалить"),
     KeyboardButton(text="Отмена"),
     KeyboardButton(text="Выход"),
     ]
], resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню ...'
)

r_kb_load_exit = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="👌 Загрузить"),
     KeyboardButton(text="🚫 Выход")
     ]
], resize_keyboard=True,
   input_field_placeholder='Выберите пункт меню ...'
)

r_kb_begin_exit = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="👌 Начать"),
     KeyboardButton(text="🚫 Выход")
     ]
], resize_keyboard=True,
   input_field_placeholder='Выберите пункт меню ...'
)

r_kb_exit = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🚫 Выход")
     ]
], resize_keyboard=True,
   input_field_placeholder='Выберите пункт меню ...'
)