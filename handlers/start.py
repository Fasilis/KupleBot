from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import FSInputFile
import os

router = Router()

def get_start_menu():
    text = (
        "🎗 <b>KupleBot — ваш помощник в мире подарков!</b>\n\n"
        "💠 Бот автоматически выкупает редкие подарки, как только они появляются.\n"
        "💎 Работает быстро, точно и без промедлений.\n\n"
        "🎟 <b>Основные возможности:</b>\n"
        "• Умные фильтры по цене, лимитам и эмиссии\n"
        "• Моментальная авто-скупка по заданным параметрам\n"
        "• Профиль с балансом, историей покупок и статусом\n"
        "✨ Просто настрой фильтры, пополни баланс — и бот начнёт работать за тебя.\n\n"
        "Выберите действие 👇 "
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Пополнить баланс", callback_data="stub_pay")],
        [InlineKeyboardButton(text="👨‍🏫 Мой профиль", callback_data="stub_profile")],
        [InlineKeyboardButton(text="⚙️ Настройки фильтров", callback_data="stub_settings")]
    ])

    return text, keyboard

async def send_start_menu(message: types.Message, with_banner: bool = True):
    text, keyboard = get_start_menu()

    if with_banner:
        banner = FSInputFile(os.path.abspath("static/KupleBotBanner.png"))
        await message.answer_photo(
            photo=banner,
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

@router.message(CommandStart())
async def start_handler(message: types.Message):
    await send_start_menu(message, with_banner=True)