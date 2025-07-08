from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import LabeledPrice

from bot import bot, supabase
from config import PROVIDER_TOKEN

router = Router()

class PaymentStates(StatesGroup):
    waiting_for_amount = State()

@router.message(Command("pay"))
async def cmd_topup(message: types.Message, state: FSMContext):
    await message.answer("Сколько звёзд пополнить?")
    await state.set_state(PaymentStates.waiting_for_amount)

@router.message(PaymentStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount_stars = int(message.text)
        if amount_stars <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("Введите корректное число больше 0.")

    prices = [LabeledPrice(label=f"Пополнение {amount_stars} звёзд", amount=amount_stars)]

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Пополнение звёзд",
        description=f"Вы пополняете {amount_stars} звёзд",
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

    await message.answer(f"Оплачено {stars} звёзд.")
    
@router.callback_query(lambda c: c.data == "stub_pay")
async def callback_topup_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Сколько звёзд пополнить?")
    await state.set_state(PaymentStates.waiting_for_amount)
    await callback.answer()

