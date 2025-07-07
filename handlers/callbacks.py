import aiohttp
from aiogram import Router, types
from bot import supabase, BOT_TOKEN

from aiogram.filters.callback_data import CallbackData

router = Router()

class RefundCallback(CallbackData, prefix="refund"):
    tx_index: int

@router.callback_query(RefundCallback.filter())
async def handle_specific_refund(callback: types.CallbackQuery, callback_data: RefundCallback):
    user_id = callback.from_user.id
    tx_index = callback_data.tx_index

    result = supabase.table("payments").select("*") \
        .eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
    data = result.data

    if not data or tx_index >= len(data):
        return await callback.answer("Транзакция не найдена.", show_alert=True)

    tx = data[tx_index]

    if tx["refunded"]:
        return await callback.answer("Эта транзакция уже рефнута.", show_alert=True)

    charge_id = tx["charge_id"]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"https://api.telegram.org/bot{BOT_TOKEN}/refundStarPayment",
                json={
                    "user_id": user_id,
                    "telegram_payment_charge_id": charge_id
                }
            ) as response:
                result_api = await response.json()

        if result_api.get("ok"):
            supabase.table("payments").update({"refunded": True}).eq("charge_id", charge_id).execute()
            await callback.message.edit_text(f"Рефнуто {tx['stars']}⭐")
        else:
            error_msg = result_api.get("description", "Ошибка при возврате средств")
            await callback.answer(f"Ошибка: {error_msg}", show_alert=True)

    except Exception as e:
        print(f"Ошибка рефанда транзакции: {e}")
        await callback.answer("Ошибка при возврате средств", show_alert=True)
