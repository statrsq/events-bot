from loguru import logger
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from src.bot.localization.translator import LocalizedTranslator
from src.bot.misc.callback_data.admin import (
    AdminMenuCallback,
    AdminSection,
    BroadcastCallback,
    BroadcastAction
)
from src.bot.misc.keyboards.admin.broadcast import (
    get_broadcast_menu_keyboard,
    get_broadcast_confirmation_keyboard
)
from src.bot.misc.keyboards.admin.menu import get_admin_menu_keyboard
from src.bot.services.notification_service import NotificationService

router = Router(name="admin_broadcast")


class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    confirmation = State()


@router.callback_query(AdminMenuCallback.filter(F.action == AdminSection.BROADCAST))
async def show_broadcast_menu(callback: CallbackQuery, translator: LocalizedTranslator):
    """Показать меню рассылки"""
    try:
        text = translator.get("broadcast_menu_title")
        keyboard = get_broadcast_menu_keyboard(translator)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка отображения меню рассылки: {e}")
        await callback.answer(translator.get("error_processing_request"), show_alert=True)


@router.callback_query(BroadcastCallback.filter(F.action == BroadcastAction.START))
async def start_broadcast(
        callback: CallbackQuery,
        state: FSMContext,
        translator: LocalizedTranslator
):
    """Начать процесс рассылки - запросить сообщение"""
    try:
        text = translator.get("broadcast_enter_message")

        await callback.message.edit_text(text)
        await state.set_state(BroadcastStates.waiting_for_message)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка начала рассылки: {e}")
        await callback.answer(translator.get("error_processing_request"), show_alert=True)


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(
        message: Message,
        state: FSMContext,
        translator: LocalizedTranslator
):
    """Обработать введенное сообщение для рассылки"""
    try:
        broadcast_text = message.text

        if not broadcast_text or broadcast_text.strip() == "":
            await message.answer(translator.get("broadcast_empty_message"))
            return

        # Сохраняем текст в состоянии
        await state.update_data(broadcast_text=broadcast_text)

        # Показываем подтверждение
        text = translator.get("broadcast_confirmation", message=broadcast_text)
        keyboard = get_broadcast_confirmation_keyboard(translator)

        await message.answer(text, reply_markup=keyboard)
        await state.set_state(BroadcastStates.confirmation)

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения рассылки: {e}")
        await message.answer(translator.get("error_processing_request"))


@router.callback_query(
    BroadcastStates.confirmation,
    BroadcastCallback.filter(F.action == BroadcastAction.CONFIRM)
)
async def confirm_broadcast(
        callback: CallbackQuery,
        state: FSMContext,
        translator: LocalizedTranslator,
):
    """Подтвердить и начать рассылку"""
    try:
        # Получаем сохраненный текст
        state_data = await state.get_data()
        broadcast_text = state_data.get('broadcast_text')

        if not broadcast_text:
            await callback.answer(translator.get("error_processing_request"), show_alert=True)
            return

        # Уведомляем о начале рассылки
        await callback.message.edit_text(translator.get("broadcast_started"))

        # Запускаем рассылку
        notification_service = NotificationService(bot=callback.bot)
        sent_count = await notification_service.broadcast_message(broadcast_text)

        # Показываем результат
        result_text = translator.get("broadcast_completed", count=sent_count)
        keyboard = get_admin_menu_keyboard(translator)

        await callback.message.answer(result_text, reply_markup=keyboard)
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка выполнения рассылки: {e}")
        await callback.answer(translator.get("error_processing_request"), show_alert=True)


@router.callback_query(BroadcastCallback.filter(F.action == BroadcastAction.CANCEL))
async def cancel_broadcast(
        callback: CallbackQuery,
        state: FSMContext,
        translator: LocalizedTranslator
):
    """Отменить рассылку"""
    try:
        await state.clear()

        text = translator.get("broadcast_cancelled")
        keyboard = get_admin_menu_keyboard(translator)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка отмены рассылки: {e}")
        await callback.answer(translator.get("error_processing_request"), show_alert=True)