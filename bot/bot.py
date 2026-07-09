#!/usr/bin/env python3
"""
frantik.by — Telegram-бот подписки и рассылки.

Что делает:
  • /start  — подписывает человека (сохраняет chat_id) и шлёт приветствие
  • /stop   — отписка
  • любое сообщение от пользователя — тоже засчитывается как подписка
  • /stats  — (админ) сколько подписчиков
  • /send <текст> — (админ) разослать сообщение всем подписчикам
  • на фото/видео с подписью от админа с началом "рассылка" — разошлёт медиа всем

Хранилище подписчиков: subscribers.json (простой файл рядом с ботом).
На Railway подключите Volume и смонтируйте на папку /data, задав DB_PATH=/data/subscribers.json,
иначе список сбросится при передеплое.

ENV:
  BOT_TOKEN  — токен от @BotFather (обязательно)
  ADMIN_ID   — ваш Telegram user id (узнать: напишите боту @userinfobot)
  SITE_URL   — ссылка на сайт (по умолчанию https://frantik.by)
  DB_PATH    — путь к файлу подписчиков (по умолчанию ./subscribers.json)
"""
import os, json, asyncio, logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          ContextTypes, filters)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

TOKEN    = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
SITE_URL = os.environ.get("SITE_URL", "https://frantik.by")
DB_PATH  = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "subscribers.json"))

WELCOME = (
    "👋 Привет! Ты подписался на <b>frantik.by</b> — детская и подростковая одежда в Минске.\n\n"
    "Будем присылать первым:\n"
    "• поступления школьной формы 2026/2027\n"
    "• новинки и акции\n"
    "• сообщим, когда приедет нужный размер\n\n"
    f"Наши магазины и каталог: {SITE_URL}\n\n"
    "Отписаться в любой момент — /stop"
)

def load():
    try:
        with open(DB_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save(d):
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)

def add_sub(user):
    subs = load()
    if str(user.id) not in subs:
        subs[str(user.id)] = {"name": user.full_name, "username": user.username}
        save(subs)
        return True
    return False

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    add_sub(update.effective_user)
    await update.message.reply_text(WELCOME, parse_mode=ParseMode.HTML)

async def stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    subs = load(); subs.pop(str(update.effective_user.id), None); save(subs)
    await update.message.reply_text("Ты отписался — больше не потревожим. Вернуться: /start")

async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"Подписчиков: {len(load())}")

async def _broadcast(ctx, sender):
    """sender(uid) -> awaitable, отправляющий контент одному подписчику"""
    subs = load(); ok = fail = 0
    for uid in list(subs):
        try:
            await sender(int(uid)); ok += 1
        except Exception as e:
            fail += 1; logging.warning("send %s failed: %s", uid, e)
        await asyncio.sleep(0.05)  # ~20 msg/сек, чтобы не ловить лимиты
    return ok, fail

async def send_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("Использование: /send <текст рассылки>")
        return
    ok, fail = await _broadcast(ctx, lambda uid: ctx.bot.send_message(uid, text, parse_mode=ParseMode.HTML))
    await update.message.reply_text(f"Разослано: {ok}, ошибок: {fail}")

async def media_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Админ шлёт фото/видео с подписью, начинающейся на 'рассылка' — разошлём всем."""
    if update.effective_user.id != ADMIN_ID:
        return
    cap = (update.message.caption or "")
    if not cap.lower().startswith("рассылка"):
        return
    body = cap[len("рассылка"):].strip()
    if update.message.photo:
        fid = update.message.photo[-1].file_id
        ok, fail = await _broadcast(ctx, lambda uid: ctx.bot.send_photo(uid, fid, caption=body, parse_mode=ParseMode.HTML))
    elif update.message.video:
        fid = update.message.video.file_id
        ok, fail = await _broadcast(ctx, lambda uid: ctx.bot.send_video(uid, fid, caption=body, parse_mode=ParseMode.HTML))
    else:
        return
    await update.message.reply_text(f"Медиа разослано: {ok}, ошибок: {fail}")

async def catch_all(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Любое сообщение = подписка (тихо), плюс дружелюбный ответ новичку."""
    if update.effective_user.id == ADMIN_ID:
        return
    if add_sub(update.effective_user):
        await update.message.reply_text(WELCOME, parse_mode=ParseMode.HTML)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("send", send_cmd))
    app.add_handler(MessageHandler((filters.PHOTO | filters.VIDEO) & filters.CAPTION, media_broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, catch_all))
    logging.info("frantik bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
