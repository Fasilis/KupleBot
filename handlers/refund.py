import aiohttp
from aiogram import Router, types
from aiogram.filters import Command
from bot import supabase, BOT_TOKEN

router = Router()

@router.message(Command("refund"))
async def manual_refund(message: types.Message):
    parts = message.text.strip().split()

    if len(parts) < 2:
        return await message.answer("Использование: /refund <charge_id>", parse_mode="Markdown")

    charge_id = parts[1]
    user_id = message.from_user.id

    result = supabase.table("payments").select("*") \
        .eq("user_id", user_id).eq("charge_id", charge_id).eq("refunded", False).execute()

    if not result.data:
        return await message.answer("Транзакция не найдена или уже рефнута.")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"https://api.telegram.org/bot{BOT_TOKEN}/refundStarPayment",
                json={"user_id": user_id, "telegram_payment_charge_id": charge_id}
            ) as resp:
                result_api = await resp.json()

        if result_api.get("ok"):
            supabase.table("payments").update({"refunded": True, "type": "refund"}).eq("charge_id", charge_id).execute()
            await message.answer("Рефанд выполнен успешно.")
        else:
            await message.answer(f"Ошибка при рефанде: {result_api.get('description')}")
    except Exception as e:
        print(f"Ошибка рефанда: {e}")
        await message.answer("Произошла ошибка при попытке рефанда.")
