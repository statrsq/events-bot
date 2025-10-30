from functools import wraps

from aiogram.fsm.context import FSMContext
from aiogram.types import Message


def throttle_message(key: str = "default"):
    """ Удаляет сообщение, если оно уже обрабатывается в хэндлере """
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, state: FSMContext, *args, **kwargs):
            # Получаем текущие данные состояния
            state_data = await state.get_data()
            if state_data.get(f"throttled_{key}"):
                try:
                    await message.delete()
                except Exception:
                    pass
                return

            # Устанавливаем флаг
            await state.update_data(**{f"throttled_{key}": True})

            try:
                kwargs.update(state=state)
                return await func(message, *args, **kwargs)
            finally:
                # Убираем флаг после выполнения
                await state.update_data(**{f"throttled_{key}": False})
        return wrapper
    return decorator
