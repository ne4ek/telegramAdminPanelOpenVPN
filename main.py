import asyncio
import logging
import subprocess
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
HOST = os.getenv('HOST', 'Не указан')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

# Создаем экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я минимальный Telegram бот.\n"
        "Используй /help для просмотра доступных команд."
    )

# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/info - Информация о сервере\n"
        "/create_user имя - Создать нового пользователя OpenVPN\n"
    )

# Обработчик команды /info
@dp.message(Command("info"))
async def cmd_info(message: Message):
    import platform
    import datetime
    
    server_info = (
        "🖥️ **Информация о сервере:**\n\n"
        f"🌐 **Хост:** `{HOST}`\n"
        f"🖥️ **Платформа:** {platform.system()} {platform.release()}\n"
        f"🐍 **Python:** {platform.python_version()}\n"
        f"⏰ **Время сервера:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"🤖 **Статус бота:** ✅ Работает"
    )
    
    await message.answer(server_info, parse_mode="Markdown")

# Обработчик команды /create_user
@dp.message(Command("create_user"))
async def cmd_create_user(message: Message):
    # Извлекаем имя пользователя из команды
    command_parts = message.text.split()
    if len(command_parts) < 2:
        await message.answer(
            "❌ **Ошибка:** Укажите имя пользователя!\n\n"
            "**Использование:** `/create_user имя_пользователя`\n"
            "**Пример:** `/create_user john_doe`",
            parse_mode="Markdown"
        )
        return
    
    username = command_parts[1].strip()
    
    # Проверяем имя пользователя на валидность
    if not username.replace('_', '').replace('-', '').isalnum():
        await message.answer(
            "❌ **Ошибка:** Имя пользователя может содержать только буквы, цифры, дефисы и подчеркивания!"
        )
        return
    
    try:
        # Отправляем сообщение о начале процесса
        status_msg = await message.answer("⏳ Создаю пользователя...")
        
        # Выполняем команду добавления пользователя через наш скрипт-обертку
        cmd = f'bash add_user.sh {username}'
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd='/app'  # Рабочая директория в контейнере
        )
        
        if result.returncode == 0:
            # Успешное создание пользователя
            await status_msg.edit_text(
                f"✅ **Пользователь успешно создан!**\n\n"
                f"👤 **Имя пользователя:** `{username}`\n"
                f"📁 **Файл конфигурации:** `{username}.ovpn`\n\n"
                f"Файл конфигурации сохранен в рабочей директории сервера.",
                parse_mode="Markdown"
            )
        else:
            # Ошибка при создании пользователя
            error_msg = result.stderr if result.stderr else "Неизвестная ошибка"
            await status_msg.edit_text(
                f"❌ **Ошибка при создании пользователя:**\n\n"
                f"**Детали:** `{error_msg}`",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка выполнения команды:**\n\n`{str(e)}`",
            parse_mode="Markdown"
        )

# Обработчик всех остальных сообщений
@dp.message()
async def echo_message(message: Message):
    await message.answer(f"Вы написали: {message.text}")

# Основная функция
async def main():
    # Удаляем webhook (если был установлен)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as e:
        print(f"Ошибка: {e}")
