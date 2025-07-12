from aiogram import Router, types, F
import aiogram
import aiogram.exceptions
from bot import bot, supabase
from handlers.filter import load_info, save_info
from datetime import datetime
import asyncio

async def check_filter(gift, balance, filters):
    limited = gift.total_count is not None

    if balance < gift.star_count:
        return False

    if not (filters['min_price'] <= gift.star_count <= filters['max_price']):
        return False

    if filters['only_limited'] != limited:
        return False

    if limited and not (filters['min_emission'] <= gift.total_count <= filters['max_emission']):
        return False

    return True



async def process_user(user_id, info, filters, sorted_gifts):
    balance = info['balance']

    while True:
        for gift in sorted_gifts:
            if await check_filter(gift, balance, filters):
                try:                
                    await bot.send_gift(gift.id, user_id)

                    balance -= gift.star_count
                    save_info(user_id, {"balance": balance})

                    supabase.table("payments").insert({
                        "user_id": user_id,
                        "type": "purchase", 
                        "charge_id": None,
                        "stars": gift.star_count, 
                        "refunded": False
                    }).execute()

                    info["balance"] = balance

                    break  
                except aiogram.exceptions.TelegramBadRequest as e:
                    if "Telegram server says - Bad Request: STARGIFT_USAGE_LIMITED" in str(e):
                        sorted_gifts.remove(gift)
                    else:
                        print(f"TelegramBadRequest: {e}")
                except Exception as e:
                    print(f"Unexpected error occurred: {e}")
        else:
            break 



async def buy_while_available(gifts):
    user_info_list = supabase.table("user_info").select("*").execute().data
    user_filters_list = supabase.table("user_filters").select("*").execute().data

    info_map = {u['user_id']: u for u in user_info_list}
    filters_map = {f['user_id']: f for f in user_filters_list}

    sorted_gifts = sorted(gifts, key=lambda g: g.star_count, reverse=True)

    while True:
        tasks = []

        for user_id, info in info_map.items():
            filters = filters_map.get(user_id)
            if not filters:
                continue

            task = asyncio.create_task(process_user(user_id, info, filters, sorted_gifts))
            tasks.append(task)

        await asyncio.gather(*tasks)


