import aiohttp
from aiogram import Router, types, F
from bot import supabase, BOT_TOKEN

from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from handlers.button_builder import build_buttons, make_tx_text

router = Router()

class RefundCallback(CallbackData, prefix="refund"):
    tx_id: str

@router.callback_query(RefundCallback.filter())
async def handle_specific_refund(callback: types.CallbackQuery, callback_data: RefundCallback):
    user_id = callback.from_user.id
    tx_id = callback_data.tx_id

    result = supabase.table("payments").select("*") \
        .eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
    tx = next((tx for tx in result.data if tx["id"] == tx_id), None)

    if not tx:
        return await callback.answer("Транзакция не найдена.", show_alert=True)


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
            supabase.table("payments").update({"refunded": True, "type":"refund"}).eq("charge_id", charge_id).execute()
            await callback.message.edit_text(f"Рефнуто {tx['stars']}⭐")
        else:
            error_msg = result_api.get("description", "Ошибка при возврате средств")
            await callback.answer(f"Ошибка: {error_msg}", show_alert=True)

    except Exception as e:
        print(f"Ошибка рефанда транзакции: {e}")
        await callback.answer("Ошибка при возврате средств", show_alert=True)



@router.callback_query(F.data.startswith("transaction_type:"))
async def handle_transaction_list(callback: CallbackQuery):
    tx_type = callback.data.split(":")[1]
    
    result = supabase.table("payments").select("*") \
            .eq("user_id", callback.message.chat.id) \
            .eq("type", tx_type) \
            .order("created_at", desc=True).execute()
    if not result.data:
        return await callback.answer("Нету транзакций")
    
    markup = build_buttons(0, result.data, f"transaction_{tx_type}:", make_tx_text, 8, 2)
    await callback.message.answer("Ваши транзакции:", reply_markup=markup)



@router.callback_query(F.data.startswith("nav_"))
async def handle_navigation(callback: CallbackQuery):
    """Handle navigation callbacks"""
    user_id = callback.from_user.id
    data = callback.data[len("nav_"):]
    if ":" not in data:
        await callback.answer("❌ Неверные данные навигации.")
        return

    callback_prefix, page = data.rsplit(":", 1)
    page = int(page)

    if callback_prefix.startswith("transaction_"):
        if "_" in callback_prefix:
            tx_type = callback_prefix.split("_")[1].rstrip(":")
            result = supabase.table("payments").select("*") \
                .eq("user_id", user_id) \
                .eq("type", tx_type) \
                .order("created_at", desc=True).execute()
            markup = build_buttons(page, result.data, f"transaction_{tx_type}:", make_text_func=make_tx_text, items_per_page=8, columns=2)
        else:
            result = supabase.table("payments").select("*") \
                .eq("user_id", user_id).order("created_at", desc=True).execute()
            markup = build_buttons(page, result.data, "transaction:", make_text_func=make_tx_text, items_per_page=8, columns=2)
    else:
        await callback.answer("❌ Невозможно отобразить.")
        return

    await callback.message.edit_reply_markup(reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("transaction"))
async def handle_transaction_item(callback: CallbackQuery):
    if callback.data.startswith("transaction_"):
        tx_id = callback.data.split(":", 1)[1]
    else:
        tx_id = callback.data.split(":", 1)[1]
    
    result = supabase.table("payments").select("*") \
            .eq("id", tx_id) \
            .order("created_at", desc=True).execute()
    
    if not result.data:
        await callback.answer("❌ Транзакция не найдена.")
        return
    
    tx = result.data[0]

    markup = InlineKeyboardMarkup(inline_keyboard=[])
    if not tx.get('refunded'):
        markup.inline_keyboard.append([
            InlineKeyboardButton(text="🔁 Вернуть звёзды", callback_data=RefundCallback(tx_id=tx['id']).pack())
        ])

    date = datetime.fromisoformat(tx['created_at']).strftime("%d.%m.%Y %H:%M") 
    text = ""
    if tx.get('type') == "deposit":
        text += f"💸 *ID Транзакции*: `{tx.get('charge_id', '-')}`\n"

    text += (
        f"💰 Сумма: {tx['stars']}⭐️\n"
        f"📅 Дата: {date} UTC\n"
    )

    if tx.get('type') == "deposit":
        text += f"🔁 Возврат: {'✅ Да' if tx.get('refunded') else '❌ Нет'}"

    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=markup
    )
    await callback.answer()