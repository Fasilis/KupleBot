from aiogram import Router, types


router = Router()


router = Router()
@router.callback_query(lambda c: c.data == "stub_settings")
async def stub_settings_handler(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Настройки фильтров пока в разработке.")
    await callback.answer()