import aiogram
import aiogram.exceptions
from bot import bot, supabase
from handlers.filter import load_info, save_info
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



async def process_user(user_id, info, filters, sorted_gifts, exhausted_gifts):
    balance = info['balance']
    
    result = supabase.table("channels").select("username").eq("user_id", user_id).execute()
    channels = [row["username"] for row in result.data]
    has_channels = bool(channels)

    current_channel_index = 0
    made_purchase = False

    while True:
        for gift_index, gift in enumerate(sorted_gifts):
            if gift.id in exhausted_gifts:
                continue
            if await check_filter(gift, balance, filters):
                try: 
                    if has_channels:
                        recipient = f"@{channels[min(gift_index, len(channels) - 1)]}"
                        await bot.send_gift(gift.id, chat_id=recipient) 
                    else:
                        recipient = user_id
                        await bot.send_gift(gift.id, user_id=recipient) 
                                    
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

                    made_purchase = True

                    break  
                except aiogram.exceptions.TelegramBadRequest as e:
                    if "STARGIFT_USAGE_LIMITED" in str(e):
                        exhausted_gifts.add(gift.id)
                        result = supabase.table("channels").select("*").eq("user_id", user_id).execute()
                        if has_channels and current_channel_index < len(channels)-1:
                            current_channel_index += 1
                        continue
                    else:
                        print(f"TelegramBadRequest: {e}")
                except Exception as e:
                    print(f"Unexpected error occurred: {e}")
            else:
                continue
        else:
            break 

    return made_purchase


async def buy_while_available(gifts):
    user_info_list = supabase.table("user_info").select("*").execute().data
    user_filters_list = supabase.table("user_filters").select("*").execute().data

    info_map = {u['user_id']: u for u in user_info_list}
    filters_map = {f['user_id']: f for f in user_filters_list}

    sorted_gifts = sorted(gifts, key=lambda g: g.star_count, reverse=True)
    exhausted_gifts = set()

    while True:
        tasks = []

        for user_id, info in info_map.items():
            filters = filters_map.get(user_id)
            if not filters:
                continue
            task = asyncio.create_task(process_user(user_id, info, filters, sorted_gifts.copy(), exhausted_gifts))
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        if all(gift.id in exhausted_gifts for gift in sorted_gifts):
            print("🎁 All gifts exhausted — stopping loop.")
            break

        if not any(results):
            print("⚠️ No purchases made — stopping loop.")
            break
