from .user_service import UserService
from .file_service import FileService
from .system_service import SystemService


class ServiceManager:
    """Менеджер сервисов для централизованного управления"""
    
    def __init__(self):
        self.user_service = UserService()
        self.file_service = FileService()
        self.system_service = SystemService()
    
    def get_user_service(self) -> UserService:
        """Получает сервис для работы с пользователями"""
        return self.user_service
    
    def get_file_service(self) -> FileService:
        """Получает сервис для работы с файлами"""
        return self.file_service
    
    def get_system_service(self) -> SystemService:
        """Получает сервис для работы с системной информацией"""
        return self.system_service
