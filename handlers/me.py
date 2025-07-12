from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import (InlineKeyboardMarkup,
                           InlineKeyboardButton, 
                           ReplyKeyboardRemove)
from bot import supabase
from handlers.start import send_start_menu
from handlers.filter import load_info, save_info



router = Router()

@router.callback_query(lambda c: c.data == "stub_profile")
async def stub_profile_handler(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐️ Мой баланс", callback_data="баланс"),
            InlineKeyboardButton(text="📂 История транзакций", callback_data="транзакции")
        ],
        [
            InlineKeyboardButton(text="🔙 Выйти", callback_data="Выйти")
        ]
    ])
    await callback.message.delete()
    await callback.message.answer(
        "👤 <b>Личный кабинет</b>\n\nВыберите действие ниже:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(lambda c: c.data in ["баланс", "транзакции", "Выйти"])
async def handle_user_menu_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data

    if data == "баланс":
        try:
            info = await load_info(user_id)
            total = info['balance']
            await callback.message.edit_text(f"💰 Ваш баланс: {total} звёзд.", reply_markup=back_to_profile_kb())
            
        except Exception as e:
            print(f"Ошибка показа баланса: {e}")
            await callback.message.edit_text("Беда, не вижу баланс", reply_markup=back_to_profile_kb())

    elif data == "транзакции":
        try:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='💶 Пополнения', callback_data='transaction_type:deposit')],
                [
                    InlineKeyboardButton(text='🛒 Покупки', callback_data='transaction_type:purchase'),
                    InlineKeyboardButton(text='⛓️‍💥 Возвраты', callback_data='transaction_type:refund')
                ],
                [InlineKeyboardButton(text='🔙 Назад', callback_data='stub_profile')]
            ])
            await callback.message.edit_text("Выбери тип транзакций:", reply_markup=markup)
        except Exception as e:
            print(f"Ошибка показа истории: {e}")
            await callback.message.edit_text("Беда, не вижу историю")
            
    elif data == "Выйти":
        await callback.message.delete() 
        await send_start_menu(callback.message, with_banner=True)
        
def back_to_profile_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="stub_profile")]
    ])