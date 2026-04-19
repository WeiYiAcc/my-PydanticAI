from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from pydanticai_orchestrator.service import OrchestratorService
from pydanticai_orchestrator.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('PydanticAI orchestrator bot is running. Commands: /doctor /hermes /pi /stokowski_status /stokowski_dryrun /route')


async def doctor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service = context.application.bot_data['service']
    await update.message.reply_text(str(service.doctor()))


async def hermes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service = context.application.bot_data['service']
    task = ' '.join(context.args).strip()
    if not task:
        await update.message.reply_text('Usage: /hermes <task>')
        return
    result = await asyncio.to_thread(service.hermes, task)
    await update.message.reply_text(result.summary)


async def pi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service = context.application.bot_data['service']
    task = ' '.join(context.args).strip()
    if not task:
        await update.message.reply_text('Usage: /pi <task>')
        return
    result = await asyncio.to_thread(service.pi, task)
    await update.message.reply_text(result.summary)


async def stokowski_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service = context.application.bot_data['service']
    result = await asyncio.to_thread(service.stokowski_status)
    await update.message.reply_text(result.summary)


async def stokowski_dryrun_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service = context.application.bot_data['service']
    result = await asyncio.to_thread(service.stokowski_dry_run)
    await update.message.reply_text(result.summary)


async def route_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service = context.application.bot_data['service']
    task = ' '.join(context.args).strip()
    if not task:
        await update.message.reply_text('Usage: /route <request>')
        return
    result = await asyncio.to_thread(service.handle_request, task)
    await update.message.reply_text(result.answer)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    service = context.application.bot_data['service']
    await update.message.chat.send_action('typing')
    result = await asyncio.to_thread(service.handle_request, update.message.text)
    await update.message.reply_text(result.answer)


def main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit('TELEGRAM_BOT_TOKEN is not set')

    service = OrchestratorService(settings)
    app = ApplicationBuilder().token(settings.telegram_bot_token).build()
    app.bot_data['service'] = service
    app.add_handler(CommandHandler('start', start_cmd))
    app.add_handler(CommandHandler('doctor', doctor_cmd))
    app.add_handler(CommandHandler('hermes', hermes_cmd))
    app.add_handler(CommandHandler('pi', pi_cmd))
    app.add_handler(CommandHandler('stokowski_status', stokowski_status_cmd))
    app.add_handler(CommandHandler('stokowski_dryrun', stokowski_dryrun_cmd))
    app.add_handler(CommandHandler('route', route_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()


if __name__ == '__main__':
    main()
