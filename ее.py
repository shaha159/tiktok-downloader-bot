from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import asyncio
import os
import json
from datetime import datetime, timedelta

API_ID = 23658294
API_HASH = "633518b64f17912bce4a8f65c4a48fb7"
BOT_TOKEN = "8057537136:AAGQC3Tlj8SPGnH1vtFOHI6vp2GA5Ej0D6M"
ADMIN_ID = 7183817298
CHANNEL_USERNAME = "testoviychannel11"

app = Client("tiktok_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

users_file = "users.json"
stats_file = "stats.json"

if not os.path.exists(users_file):
    with open(users_file, "w") as f:
        json.dump([], f)

if not os.path.exists(stats_file):
    with open(stats_file, "w") as f:
        json.dump({}, f)

def save_user(user_id):
    with open(users_file, "r") as f:
        users = json.load(f)
    if user_id not in users:
        users.append(user_id)
        with open(users_file, "w") as f:
            json.dump(users, f)

def get_users():
    with open(users_file, "r") as f:
        return json.load(f)

def save_download_stat():
    today_str = datetime.now().strftime("%Y-%m-%d")
    with open(stats_file, "r") as f:
        stats = json.load(f)

    stats[today_str] = stats.get(today_str, 0) + 1

    with open(stats_file, "w") as f:
        json.dump(stats, f)

def get_download_stats():
    with open(stats_file, "r") as f:
        stats = json.load(f)

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    total = sum(stats.values())
    today_count = stats.get(today.strftime("%Y-%m-%d"), 0)
    yesterday_count = stats.get(yesterday.strftime("%Y-%m-%d"), 0)
    week_count = sum(count for day, count in stats.items() if datetime.strptime(day, "%Y-%m-%d").date() >= week_ago)
    month_count = sum(count for day, count in stats.items() if datetime.strptime(day, "%Y-%m-%d").date() >= month_ago)

    return total, today_count, yesterday_count, week_count, month_count

async def check_subscription(user_id):
    try:
        member = await app.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status not in ("left", "kicked")
    except Exception as e:
        print(f"[ERROR] Ошибка проверки подписки: {e}")
        return False

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user_id = message.from_user.id
    save_user(user_id)

    if not await check_subscription(user_id):
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔔 Перейти в канал", url=f"https://t.me/{CHANNEL_USERNAME}")]]
        )
        await message.reply(
            "❗ Для использования бота нужно подписаться на наш канал.\n"
            "Пожалуйста, подпишитесь и нажмите /start снова.",
            reply_markup=keyboard
        )
        return

    await message.reply(
        "**👋 Привет!**\n\nОтправь ссылку на видео из TikTok, и я скачаю его без водяного знака.\n\n"
        "📬 По вопросам сотрудничества: @shaha159",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
                [InlineKeyboardButton("📬 Связь с админом", url="https://t.me/shaha159")]
            ]
        ),
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_callback_query()
async def callback(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    print(f"[LOG] Callback data: {data} от user_id={user_id}")

    if data == "help":
        await callback_query.message.edit(
            "**📌 Инструкция:**\n\nПросто пришли мне ссылку на TikTok-видео, и я скачаю его без водяного знака. Видео до 50 MB.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        await callback_query.answer()
    elif data == "back":
        await callback_query.message.edit(
            "**👋 Привет!**\n\nОтправь ссылку на видео из TikTok, и я скачаю его без водяного знака.\n\n"
            "📬 По вопросам сотрудничества: @shaha159",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
                    [InlineKeyboardButton("📬 Связь с админом", url="https://t.me/shaha159")]
                ]
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        await callback_query.answer()
    else:
        await callback_query.answer()

@app.on_message(filters.text & filters.private & ~filters.command(["admin", "stats", "send"]))
async def download_tiktok(client, message: Message):
    user_id = message.from_user.id
    save_user(user_id)

    if not await check_subscription(user_id):
        await message.reply(
            f"❗ Для использования бота нужно подписаться на канал @{CHANNEL_USERNAME}.\n"
            "Пожалуйста, подпишитесь и попробуйте снова."
        )
        return

    url = message.text.strip()
    if not ("tiktok.com" in url or "vm.tiktok.com" in url):
        return await message.reply("🚫 Это не ссылка TikTok.")

    msg = await message.reply("📥 Загружаю видео...")

    try:
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': f'{DOWNLOAD_DIR}/%(title).50s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'max_filesize': 50 * 1024 * 1024,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await client.send_video(
            chat_id=message.chat.id,
            video=filename,
            caption=f"✅ Готово!\n📥 Видео: {info.get('title', 'Без названия')}"
        )
        save_download_stat()
        os.remove(filename)

    except yt_dlp.utils.DownloadError as e:
        await msg.edit(f"❌ Ошибка при скачивании: {str(e)}")
        print(f"[ERROR] DownloadError: {e}")
    except Exception as e:
        await msg.edit(f"⚠️ Что-то пошло не так:\n`{e}`")
        print(f"[ERROR] Exception при скачивании: {e}")

@app.on_message(filters.command("admin"))
async def admin_panel(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        total_users = len(get_users())
        total, today_count, yesterday_count, week_count, month_count = get_download_stats()

        await message.reply(
            "🛠 *Админ-панель*\n\n"
            f"👤 Пользователей: *{total_users}*\n"
            f"📥 Всего скачано видео: *{total}*\n\n"
            f"📅 Сегодня: *{today_count}*\n"
            f"📅 Вчера: *{yesterday_count}*\n"
            f"📅 За неделю: *{week_count}*\n"
            f"📅 За месяц: *{month_count}*\n\n"
            "Команды:\n"
            "/send - Рассылка\n"
            "/stats - Статистика",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        print(f"[ERROR] Ошибка в /admin: {e}")

@app.on_message(filters.command("stats"))
async def stats(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    total_users = len(get_users())
    total, today_count, yesterday_count, week_count, month_count = get_download_stats()

    await message.reply(
        "📊 *Статистика*\n\n"
        f"👤 Пользователей: *{total_users}*\n"
        f"📥 Всего скачано видео: *{total}*\n\n"
        f"📅 Сегодня: *{today_count}*\n"
        f"📅 Вчера: *{yesterday_count}*\n"
        f"📅 За неделю: *{week_count}*\n"
        f"📅 За месяц: *{month_count}*",
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.command("send"))
async def broadcast(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.reply("✉️ Введи текст для рассылки:")

    try:
        response = await client.listen(message.chat.id, timeout=60)
        text = response.text
        users = get_users()

        count = 0
        for user_id in users:
            try:
                await client.send_message(user_id, text)
                count += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[WARN] Не удалось отправить сообщение user_id={user_id}: {e}")

        await message.reply(f"✅ Отправлено {count} пользователям.")
    except asyncio.TimeoutError:
        await message.reply("⌛ Время ожидания истекло. Отправка отменена.")
    except Exception as e:
        print(f"[ERROR] Ошибка в рассылке: {e}")
        await message.reply(f"❌ Ошибка: {e}")

app.run()