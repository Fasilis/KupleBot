from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(CommandStart())
async def start_handler(message: types.Message):
    text = (
        "👋 Добро пожаловать!\n\n"
        "Этот бот предназначен для автоматической скупки подарков.\n\n"
        "В РАЗРАБОТКЕ\n\n"
        "Выберите действие:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Пополнить баланс", callback_data="stub_view")],
        [InlineKeyboardButton(text="👨‍🏫 Мои профиль", callback_data="stub_profile")],
        [InlineKeyboardButton(text="⚙️ Настройки фильтров", callback_data="stub_settings")]
    ])

    await message.answer(text, reply_markup=keyboard)
