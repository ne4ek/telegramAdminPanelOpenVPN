import platform
import datetime
import os
from typing import Dict


class SystemService:
    """Сервис для работы с системной информацией"""
    
    def __init__(self, host: str = None):
        self.host = host or os.getenv('HOST', 'Не указан')
    
    def get_system_info(self) -> Dict[str, str]:
        """
        Получает информацию о системе
        
        Returns:
            Dict[str, str]: Словарь с информацией о системе
        """
        try:
            return {
                'host': self.host,
                'platform': f"{platform.system()} {platform.release()}",
                'python_version': platform.python_version(),
                'current_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'bot_status': '✅ Работает'
            }
        except Exception as e:
            return {
                'error': f"Ошибка при получении системной информации: {str(e)}"
            }
    
    def format_system_info(self) -> str:
        """
        Форматирует системную информацию для отправки в Telegram
        
        Returns:
            str: Отформатированная строка с информацией о системе
        """
        info = self.get_system_info()
        
        if 'error' in info:
            return f"❌ **Ошибка:** {info['error']}"
        
        return (
            "🖥️ **Информация о сервере:**\n\n"
            f"🌐 **Хост:** `{info['host']}`\n"
            f"🖥️ **Платформа:** {info['platform']}\n"
            f"🐍 **Python:** {info['python_version']}\n"
            f"⏰ **Время сервера:** {info['current_time']}\n"
            f"🤖 **Статус бота:** {info['bot_status']}"
        )
