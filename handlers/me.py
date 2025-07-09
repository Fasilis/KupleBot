from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import (InlineKeyboardMarkup,
                           InlineKeyboardButton, 
                           ReplyKeyboardRemove)
from bot import supabase
from handlers.start import get_start_menu
from handlers.filter import load_info, save_info


router = Router()

@router.callback_query(lambda c: c.data == "stub_profile")
async def stub_profile_handler(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💸 Балик", callback_data="Балик"),
            InlineKeyboardButton(text="💳 История транз", callback_data="История транз")
        ],
        [
            InlineKeyboardButton(text="🔙 Выйти", callback_data="Выйти")
        ]
    ])
    await callback.message.edit_text("Личный кабинет", reply_markup=kb)
    await callback.answer()



@router.callback_query(lambda c: c.data in ["Балик", "История транз", "Выйти"])
async def handle_user_menu_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if data == "Балик":
        try:
            info = await load_info(user_id)
            total = info['balance']
            await callback.message.edit_text(f"💰 Ваш баланс: {total} звёзд.")
        except Exception as e:
            print(f"Ошибка показа баланса: {e}")
            await callback.message.edit_text("Беда, не вижу баланс")

    elif data == "История транз":
        try:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Пополнения', callback_data='transaction_type:deposit')],
                [
                    InlineKeyboardButton(text='Покупки', callback_data='transaction_type:purchase'),
                    InlineKeyboardButton(text='Возвраты', callback_data='transaction_type:refund')
                ]
            ])
            await callback.message.edit_text("Выбери тип транзакций:", reply_markup=markup)
        except Exception as e:
            print(f"Ошибка показа истории: {e}")
            await callback.message.edit_text("Беда, не вижу историю")
            
    elif data == "Выйти":
        text, keyboard = get_start_menu()
        await callback.message.edit_text(text, reply_markup=keyboard)