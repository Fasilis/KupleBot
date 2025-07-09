from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot, supabase
from config import PROVIDER_TOKEN

from handlers.start import send_start_menu 
from handlers.filter import load_info, save_info

router = Router()

class PaymentStates(StatesGroup):
    waiting_for_amount = State()

async def send_payment_menu(chat_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Выйти", callback_data="exit_to_main")]
    ])
    await bot.send_message(chat_id, "Укажите количество звёзд для пополнения баланса ⭐️", reply_markup=kb)

@router.callback_query(lambda c: c.data == "stub_pay")
async def callback_topup_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await send_payment_menu(callback.message.chat.id)
    await state.set_state(PaymentStates.waiting_for_amount)
    await callback.answer()

@router.callback_query(lambda c: c.data == "exit_to_main")
async def exit_to_main_from_payment(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await send_start_menu(callback.message, with_banner=True)
    await state.clear()
    await callback.answer()

@router.message(PaymentStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount_stars = int(message.text)
        if amount_stars <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("Введите корректное число больше 0.")

    prices = [LabeledPrice(label=f"Пополнение {amount_stars} ⭐️", amount=amount_stars)]

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Пополнение звёзд",
        description=f"Вы пополняете {amount_stars} ⭐️",
        payload=f"topup_{message.from_user.id}_{amount_stars}",
        provider_token=PROVIDER_TOKEN,
        currency="XTR",
        prices=prices,
        start_parameter="topup"
    )
    await state.clear()

@router.pre_checkout_query()
async def pre_checkout_handler(query: types.PreCheckoutQuery):
    await query.answer(ok=True)

@router.message(lambda m: m.successful_payment is not None)
async def successful_payment_handler(message: types.Message):
    payment = message.successful_payment
    user_id = message.from_user.id
    charge_id = payment.telegram_payment_charge_id
    stars = payment.total_amount

    supabase.table("payments").insert({
        "user_id": user_id,
        "type": "deposit", 
        "charge_id": charge_id,
        "stars": stars, 
        "refunded": False
    }).execute()


    info = await load_info(user_id)
    updated_balance = info['balance'] + stars
    save_info(user_id, {"balance": updated_balance})

    await message.answer(f"Оплачено {stars} ⭐️")
    await send_start_menu(message, with_banner=True)
    
@router.callback_query(lambda c: c.data == "stub_pay")
async def callback_topup_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Сколько звёзд пополнить?")
    await state.set_state(PaymentStates.waiting_for_amount)
    await callback.answer()

