from aiogram import Router, types
from aiogram.filters import Command
from bot import bot, supabase

from aiogram.enums import ParseMode

router = Router()

@router.message(Command("list"))
async def cmd_list(message: types.Message):
    try:
        gifts = await bot.get_available_gifts()
        if not gifts.gifts:
            return await message.answer("Сейчас нет доступных подарков.")

        lines = ["*Доступные подарки:*", ""]
        for i, gift in enumerate(gifts.gifts, 1):
            lines.append(f"{i}. {gift.sticker.emoji}  `{gift.id}` — ⭐ {gift.star_count}")

        await message.reply("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        print(f"Ошибка при получении списка подарков: {e}")
        await message.answer("Не удалось получить список подарков.")

@router.message(Command("send"))
async def cmd_send_gift(message: types.Message):
    args = message.text.split()

    if len(args) < 3:
        return await message.answer("Использование: /send <user_id> <gift_id>")

    try:
        gifts = await bot.get_available_gifts()
        user_id = int(args[1])
        gift_id = args[2]
        stars = next((s for s in gifts.gifts if s["id"] == gift_id), None).star_count

        ok = await bot.send_gift(
            user_id=user_id,
            gift_id=gift_id,
            text="..."
        )

        if ok:
            await message.reply("Подарок отправлен!")
            supabase.table("payments").insert({
                "user_id": user_id,
                "type": "deposit", 
                "charge_id": None,
                "stars": stars, 
                "refunded": False
            }).execute()
        else:
            await message.reply("Не удалось отправить подарок.")
    except Exception as e:
        print(f"Ошибка при отправке подарка: {e}")
        await message.reply("Ошибка при отправке подарка.")

@router.message(Command("god_ref"))
async def manual_refund_direct(message: types.Message):
    parts = message.text.strip().split()

    if len(parts) < 2:
        return await message.answer("/god_ref <telegram_payment_charge_id>", parse_mode="Markdown")

    charge_id = parts[1]
    user_id = message.from_user.id

    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"https://api.telegram.org/bot{bot.token}/refundStarPayment",
                json={"user_id": user_id, "telegram_payment_charge_id": charge_id}
            ) as resp:
                result_api = await resp.json()

        if result_api.get("ok"):
            await message.answer(f"Рефанд выполнен успешно")
        else:
            await message.answer(f"Ошибка при рефанде: {result_api.get('description')}")

    except Exception as e:
        print(f"Ошибка прямого рефанда: {e}")
        await message.answer("Произошла ошибка при попытке прямого рефанда.")
