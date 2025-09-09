import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, CallbackQuery
from dotenv import load_dotenv
from services.service_manager import ServiceManager
import os

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

# Создаем экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Создаем менеджер сервисов
service_manager = ServiceManager()

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
    system_service = service_manager.get_system_service()
    server_info = system_service.format_system_info()
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
    
    try:
        # Отправляем сообщение о начале процесса
        status_msg = await message.answer("⏳ Создаю пользователя...")
        
        # Используем сервис для создания пользователя
        user_service = service_manager.get_user_service()
        success, message_text = user_service.create_user(username)
        
        if success:
            # Обновляем сообщение о успешном создании
            await status_msg.edit_text(
                f"✅ **{message_text}**\n\n"
                f"👤 **Имя пользователя:** `{username}`\n"
                f"📁 **Файл конфигурации:** `{username}.ovpn`\n\n"
                f"⏳ Отправляю файл конфигурации...",
                parse_mode="Markdown"
            )
            
            # Получаем путь к созданному файлу
            file_success, file_path, file_error = user_service.get_user_file(username)
            
            if file_success:
                try:
                    # Создаем объект файла для отправки
                    file_to_send = FSInputFile(file_path, filename=f"{username}.ovpn")
                    
                    # Отправляем файл
                    await message.answer_document(
                        document=file_to_send,
                        caption=f"📁 **{username}** - Конфигурация OpenVPN\n\n"
                               f"✅ Пользователь создан и файл готов к использованию!"
                    )
                    
                    # Обновляем статус сообщение
                    await status_msg.edit_text(
                        f"✅ **{message_text}**\n\n"
                        f"👤 **Имя пользователя:** `{username}`\n"
                        f"📁 **Файл конфигурации:** `{username}.ovpn`\n\n"
                        f"📤 **Файл отправлен выше!**",
                        parse_mode="Markdown"
                    )
                    
                except Exception as e:
                    await status_msg.edit_text(
                        f"✅ **{message_text}**\n\n"
                        f"👤 **Имя пользователя:** `{username}`\n"
                        f"📁 **Файл конфигурации:** `{username}.ovpn`\n\n"
                        f"⚠️ **Файл создан, но не удалось отправить:** `{str(e)}`",
                        parse_mode="Markdown"
                    )
            else:
                await status_msg.edit_text(
                    f"✅ **{message_text}**\n\n"
                    f"👤 **Имя пользователя:** `{username}`\n"
                    f"📁 **Файл конфигурации:** `{username}.ovpn`\n\n"
                    f"⚠️ **Файл создан, но не найден для отправки:** `{file_error}`",
                    parse_mode="Markdown"
                )
        else:
            await status_msg.edit_text(
                f"❌ **Ошибка при создании пользователя:**\n\n"
                f"**Детали:** `{message_text}`",
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
        # Используем сервис для получения списка пользователей
        user_service = service_manager.get_user_service()
        success, users, error_message = user_service.get_all_users()
        
        if not success:
            await message.answer(f"❌ **Ошибка:** {error_message}")
            return
        
        if not users:
            await message.answer("📁 **Список пользователей пуст**\n\nПока нет созданных .ovpn файлов.")
            return
        
        # Показываем первую страницу
        await show_users_page(message, users, 0)
                
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка при получении списка пользователей:**\n\n`{str(e)}`",
            parse_mode="Markdown"
        )

# Функция для отображения страницы пользователей
async def show_users_page(message: Message, users: list, page: int = 0, edit_message: bool = False):
    try:
        # Используем сервис для работы с файлами
        file_service = service_manager.get_file_service()
        
        # Создаем текст списка пользователей
        users_list = file_service.create_files_list_text(users, page)
        
        # Создаем клавиатуру с пагинацией
        keyboard = file_service.create_pagination_keyboard(users, page)
        
        if edit_message:
            await message.edit_text(users_list, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(users_list, parse_mode="Markdown", reply_markup=keyboard)
                
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка при отображении страницы:**\n\n`{str(e)}`",
            parse_mode="Markdown"
        )

# Обработчик нажатий на кнопки скачивания
@dp.callback_query(lambda c: c.data.startswith('download_'))
async def process_download_callback(callback_query: CallbackQuery):
    try:
        # Извлекаем имя пользователя из callback_data
        username = callback_query.data.replace('download_', '')
        
        # Используем сервис для получения файла пользователя
        user_service = service_manager.get_user_service()
        success, file_path, error_message = user_service.get_user_file(username)
        
        if not success:
            await callback_query.answer(f"❌ {error_message}", show_alert=True)
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

# Обработчик нажатий на кнопки пагинации
@dp.callback_query(lambda c: c.data.startswith('page_'))
async def process_page_callback(callback_query: CallbackQuery):
    try:
        # Извлекаем номер страницы из callback_data
        page_data = callback_query.data.replace('page_', '')
        
        if page_data == "info":
            await callback_query.answer("ℹ️ Информация о текущей странице", show_alert=False)
            return
        
        page = int(page_data)
        
        # Получаем список всех пользователей через сервис
        user_service = service_manager.get_user_service()
        success, users, error_message = user_service.get_all_users()
        
        if not success:
            await callback_query.answer(f"❌ {error_message}", show_alert=True)
            return
        
        # Показываем нужную страницу
        await show_users_page(callback_query.message, users, page, edit_message=True)
        
        # Подтверждаем нажатие кнопки
        await callback_query.answer(f"📄 Страница {page + 1}")
        
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
