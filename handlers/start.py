from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

def get_start_menu():
    text = (
        "👋 Добро пожаловать!\n\n"
        "Этот бот предназначен для автоматической скупки подарков.\n\n"
        "В РАЗРАБОТКЕ\n\n"
        "Выберите действие:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Пополнить баланс", callback_data="stub_pay")],
        [InlineKeyboardButton(text="👨‍🏫 Мой профиль", callback_data="stub_profile")],
        [InlineKeyboardButton(text="⚙️ Настройки фильтров", callback_data="stub_settings")]
    ])

    return text, keyboard

@router.message(CommandStart())
async def start_handler(message: types.Message):
    text, keyboard = get_start_menu()
    await message.answer(text, reply_markup=keyboard)
