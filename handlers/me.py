from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from bot import supabase





router = Router()

@router.message(Command("me"))
async def open_user_menu(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💸 Балик")],
            [KeyboardButton(text="💳 История транз")],
            [KeyboardButton(text="🔙 Выйти")]
        ],
        resize_keyboard=True
    )
    await message.answer("Личный кабинет", reply_markup=kb)

@router.message(lambda m: m.text in ["💸 Балик", "💳 История транз", "🔙 Выйти"])
async def handle_user_menu(message: types.Message):
    user_id = message.from_user.id

    if message.text == "💸 Балик":
        try:
            result = supabase.table("payments").select("*") \
                .eq("user_id", user_id).eq("refunded", False).execute()
            total = sum(tx["stars"] for tx in result.data)
            await message.answer(f"💰 Ваш баланс: {total} звёзд.")
        except Exception as e:
            print(f"Ошибка показа баланса: {e}")
            await message.answer("Беда, не вижу баланс")

    elif message.text == "💳 История транз":
        try:
            markup = InlineKeyboardMarkup(inline_keyboard=[])
            buttons_row_1 = [InlineKeyboardButton(text='Пополнения', callback_data='transaction_type:deposit')]
            buttons_row_2 = [InlineKeyboardButton(text='Покупки', callback_data='transaction_type:purchase'), InlineKeyboardButton(text='Возвраты', callback_data='transaction_type:refund')]
            markup.inline_keyboard.append(buttons_row_1)
            markup.inline_keyboard.append(buttons_row_2)
            await message.answer("Выбери тип транзакций:", reply_markup=markup)


        except Exception as e:
            print(f"Ошибка показа истории: {e}")
            await message.answer("Беда, не вижу историю")

    elif message.text == "🔙 Выйти":
        await message.answer("Скрыто", reply_markup=ReplyKeyboardRemove())
