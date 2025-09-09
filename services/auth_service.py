import os
from typing import List, Set
from functools import wraps
from aiogram.types import Message, CallbackQuery


class AuthService:
    """Сервис для авторизации пользователей"""
    
    def __init__(self):
        self.allowed_users = self._load_allowed_users()
    
    def _load_allowed_users(self) -> Set[int]:
        """
        Загружает список разрешенных пользователей из переменных окружения
        
        Returns:
            Set[int]: Множество ID разрешенных пользователей
        """
        allowed_users_str = os.getenv('ALLOWED_USERS', '')
        
        if not allowed_users_str:
            return set()
        
        try:
            # Разбираем строку по запятым и преобразуем в int
            user_ids = [int(uid.strip()) for uid in allowed_users_str.split(',') if uid.strip()]
            return set(user_ids)
        except ValueError:
            # Если есть ошибка в формате, возвращаем пустое множество
            return set()
    
    def is_user_allowed(self, user_id: int) -> bool:
        """
        Проверяет, разрешен ли пользователь
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            bool: True если пользователь разрешен, False иначе
        """
        # Если список пустой, разрешаем всем (для обратной совместимости)
        if not self.allowed_users:
            return True
        
        return user_id in self.allowed_users
    
    def get_unauthorized_message(self) -> str:
        """
        Возвращает сообщение для неавторизованных пользователей
        
        Returns:
            str: Сообщение об отказе в доступе
        """
        return (
            "🚫 **Доступ запрещен!**\n\n"
            "У вас нет прав для использования этого бота.\n"
            "Обратитесь к администратору для получения доступа."
        )


def require_auth(func):
    """
    Декоратор для проверки авторизации пользователя
    
    Применяется к обработчикам команд, которые требуют авторизации
    """
    @wraps(func)
    async def wrapper(message_or_callback, *args, **kwargs):
        # Получаем ID пользователя
        if isinstance(message_or_callback, Message):
            user_id = message_or_callback.from_user.id
            send_func = message_or_callback.answer
        elif isinstance(message_or_callback, CallbackQuery):
            user_id = message_or_callback.from_user.id
            send_func = message_or_callback.message.answer
        else:
            # Если не можем определить тип, пропускаем проверку
            return await func(message_or_callback, *args, **kwargs)
        
        # Создаем экземпляр сервиса авторизации
        auth_service = AuthService()
        
        # Проверяем авторизацию
        if not auth_service.is_user_allowed(user_id):
            await send_func(auth_service.get_unauthorized_message(), parse_mode="Markdown")
            return
        
        # Если пользователь авторизован, выполняем функцию
        return await func(message_or_callback, *args, **kwargs)
    
    return wrapper


def public_command(func):
    """
    Декоратор для публичных команд (доступны всем)
    
    Применяется к командам start, help и другим публичным
    """
    @wraps(func)
    async def wrapper(message_or_callback, *args, **kwargs):
        # Публичные команды доступны всем без проверки
        return await func(message_or_callback, *args, **kwargs)
    
    return wrapper
