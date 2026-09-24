import os
import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from yt_dlp import YoutubeDL

TOKEN = "8362184916:AAGleP9hPrBxwzwbmvKg_7I1NhkozBjBqPA"

bot = Bot(token=TOKEN)
dp = Dispatcher()

URL_REGEX = re.compile(r'https?://[^\s]+')

def download_media(url: str) -> str:
    """Завантажує відео за допомогою yt-dlp з налаштуваннями обходу захисту."""
    output_template = 'downloads/%(id)s.%(ext)s'
    os.makedirs('downloads', exist_ok=True)
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_template,
        'max_filesize': 50 * 1024 * 1024,
        'noplaylist': True,
        # Додаємо параметри, щоб обійти блокування TikTok
        'extractor_args': {'tiktok': {'webpage_download': True}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привіт! Надішли мені посилання на відео з **TikTok**, **Instagram** або **YouTube**, "
        "і я завантажу його сюди файлом."
    )

@dp.message()
async def handle_links(message: types.Message):
    if not message.text:
        return
    
    match = URL_REGEX.search(message.text)
    if not match:
        return
    
    url = match.group(0)
    
    supported_keywords = ['tiktok.com', 'instagram.com', 'instagr.am', 'youtube.com', 'youtu.be', 'vt.tiktok.com']
    if not any(keyword in url for keyword in supported_keywords):
        return

    status_msg = await message.answer("⏳ Завантажую відео...")
    
    file_path = None
    try:
        file_path = await asyncio.to_thread(download_media, url)
        
        if os.path.getsize(file_path) > 50 * 1024 * 1024:
            await status_msg.edit_text("❌ Відео занадто велике (перевищує ліміт ботів у 50 МБ).")
            return

        video_file = types.FSInputFile(file_path)
        await message.answer_video(video=video_file, caption=f"🔗 Джерело: {url}")
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Не вдалося завантажити відео.\nПомилка: {str(e)}")
        print(f"Помилка завантаження: {e}")
    
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

async def main():
    print("Бот запущено і готовий до роботи...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
