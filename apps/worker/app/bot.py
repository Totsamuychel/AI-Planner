import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import get_settings

log = logging.getLogger("worker.bot")

settings = get_settings()
dp = Dispatcher()

# Provide a mock token if none is given so the worker doesn't crash, 
# although start_polling will fail if we try to connect with a fake token.
_token = settings.telegram_bot_token or "12345:fake-token"

bot = Bot(token=_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "🤖 <b>NeuroPlan Bot</b>\n\n"
        "Available commands:\n"
        "/today - Get today's plan\n"
        "/tasks - List active tasks\n"
        "/focus - Start a focus session\n"
        "/done - Mark task as done\n"
        "/snooze - Snooze a task\n"
        "/plan - Generate schedule\n"
        "/help - This message"
    )
    await message.answer(text)


@dp.message(Command("today"))
async def cmd_today(message: Message) -> None:
    await message.answer("Here is your plan for today:\n<i>(Not implemented yet)</i>")


@dp.message(Command("tasks"))
async def cmd_tasks(message: Message) -> None:
    await message.answer("Here are your active tasks:\n<i>(Not implemented yet)</i>")


@dp.message(Command("focus"))
async def cmd_focus(message: Message) -> None:
    await message.answer("Starting focus session...\n<i>(Not implemented yet)</i>")


@dp.message(Command("done"))
async def cmd_done(message: Message) -> None:
    await message.answer("Send me the task ID to mark as done:\n<i>(Not implemented yet)</i>")


@dp.message(Command("snooze"))
async def cmd_snooze(message: Message) -> None:
    await message.answer("Send me the task ID to snooze:\n<i>(Not implemented yet)</i>")


@dp.message(Command("plan"))
async def cmd_plan(message: Message) -> None:
    await message.answer("Rebuilding today's plan...\n<i>(Not implemented yet)</i>")


async def start_bot() -> None:
    if not settings.telegram_bot_token:
        log.warning("TELEGRAM_BOT_TOKEN not set. Skipping Telegram bot polling.")
        return
    log.info("Starting Telegram bot polling...")
    await dp.start_polling(bot)
