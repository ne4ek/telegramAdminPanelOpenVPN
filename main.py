import asyncio
import logging
import subprocess
import os
import glob
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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
        "/get_all_users - Получить список всех пользователей и их .ovpn файлы\n"
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

# Обработчик команды /get_all_users
@dp.message(Command("get_all_users"))
async def cmd_get_all_users(message: Message):
    try:
        # Путь к директории с .ovpn файлами
        ovpn_dir = "/root/ovpns"
        
        # Проверяем существование директории
        if not os.path.exists(ovpn_dir):
            await message.answer("❌ **Ошибка:** Директория с .ovpn файлами не найдена!")
            return
        
        # Получаем список всех .ovpn файлов
        ovpn_files = glob.glob(os.path.join(ovpn_dir, "*.ovpn"))
        
        if not ovpn_files:
            await message.answer("📁 **Список пользователей пуст**\n\nПока нет созданных .ovpn файлов.")
            return
        
        # Сортируем файлы по имени
        ovpn_files.sort()
        
        # Формируем список пользователей
        users_list = "👥 **Список пользователей OpenVPN:**\n\n"
        
        # Создаем кнопки для каждого файла
        keyboard_buttons = []
        
        for i, file_path in enumerate(ovpn_files, 1):
            filename = os.path.basename(file_path)
            username = filename.replace('.ovpn', '')
            
            # Получаем размер файла
            file_size = os.path.getsize(file_path)
            size_kb = file_size / 1024  # Размер в KB
            
            users_list += f"{i}. **{username}** ({size_kb:.1f} KB)\n"
            
            # Создаем кнопку для скачивания файла
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"📁 {username}",
                    callback_data=f"download_{username}"
                )
            ])
        
        users_list += f"\n📊 **Всего пользователей:** {len(ovpn_files)}\n\n"
        users_list += "💡 **Нажмите на кнопку ниже для скачивания файла:**"
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await message.answer(users_list, parse_mode="Markdown", reply_markup=keyboard)
                
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка при получении списка пользователей:**\n\n`{str(e)}`",
            parse_mode="Markdown"
        )

# Обработчик нажатий на кнопки скачивания
@dp.callback_query(lambda c: c.data.startswith('download_'))
async def process_download_callback(callback_query: CallbackQuery):
    try:
        # Извлекаем имя пользователя из callback_data
        username = callback_query.data.replace('download_', '')
        
        # Путь к файлу
        file_path = f"/root/ovpns/{username}.ovpn"
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            await callback_query.answer("❌ Файл не найден!", show_alert=True)
            return
        
        # Создаем объект файла для отправки
        file_to_send = FSInputFile(file_path, filename=f"{username}.ovpn")
        
        # Отправляем файл
        await callback_query.message.answer_document(
            document=file_to_send,
            caption=f"📁 **{username}** - Конфигурация OpenVPN"
        )
        
        # Подтверждаем нажатие кнопки
        await callback_query.answer(f"✅ Файл {username}.ovpn отправлен!")
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

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
