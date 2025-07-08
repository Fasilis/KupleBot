from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from bot import supabase
from typing import List


def build_buttons(page: int, items: List, callback: str, make_text_func, items_per_page: int,
                  columns: int) -> InlineKeyboardMarkup:
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    builder = InlineKeyboardMarkup(inline_keyboard=[])

    page_items = make_text_func(items)[start_idx:end_idx]

    buttons = []
    for item, text in zip(items[start_idx:end_idx], page_items):
        if callback == 'transaction_type:':
            item_id = item['type']
        elif callback.startswith('transaction'):
            item_id = item['id']
        
        buttons.append(InlineKeyboardButton(text=text, callback_data=f"{callback}{item_id}"))

    for i in range(0, len(buttons), columns):
        row = buttons[i:i + columns]
        builder.inline_keyboard.append(row)

    total_pages = (len(items) + items_per_page - 1) // items_per_page
    nav_buttons = []

    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"nav_{callback}{page - 1}"))
    else:
        nav_buttons.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    nav_buttons.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))

    if end_idx < len(items):
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"nav_{callback}{page + 1}"))
    else:
        nav_buttons.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    builder.inline_keyboard.append(nav_buttons)
    return builder



def make_tx_text(txs):
    type = {
        'deposit': 'Депозит',
        'refund': 'Возврат',
        'purchase': 'Покупка'
    }
    return [
        f"{'+' if tx['type'] == 'deposit' else '-'}{tx['stars']}⭐️ | {type.get(tx['type'], tx['type'])}"
        for tx in txs
    ]