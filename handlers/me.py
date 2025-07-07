from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from bot import supabase
from handlers.callbacks import RefundCallback

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
            result = supabase.table("payments").select("*") \
                .eq("user_id", user_id).order("created_at", desc=True).execute()
            if not result.data:
                return await message.answer("Нету транзакций")

            lines = []
            buttons = []

            for i, tx in enumerate(result.data[:10]):
                status = "РЕФНУТО ❌" if tx["refunded"] else "АКТИВНА ✅"
                lines.append(f"• {tx['stars']} ⭐ — {status}")
                if not tx["refunded"]:
                    buttons.append([
                        InlineKeyboardButton(
                            text=f"Рефнуть {tx['stars']}⭐",
                            callback_data=RefundCallback(tx_index=i).pack()
                        )
                    ])

            text = "💳 История:\n" + "\n".join(lines)
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
            await message.answer(text, reply_markup=keyboard)

        except Exception as e:
            print(f"Ошибка показа истории: {e}")
            await message.answer("Беда, не вижу историю")

    elif message.text == "🔙 Выйти":
        await message.answer("Скрыто", reply_markup=ReplyKeyboardRemove())
