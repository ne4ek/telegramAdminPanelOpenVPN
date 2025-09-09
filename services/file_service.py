import os
from typing import List, Dict, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class FileService:
    """Сервис для работы с файлами и пагинацией"""
    
    def __init__(self, files_per_page: int = 10):
        self.files_per_page = files_per_page
    
    def create_pagination_keyboard(self, files: List[Dict], current_page: int = 0) -> InlineKeyboardMarkup:
        """
        Создает клавиатуру с пагинацией для списка файлов
        
        Args:
            files: Список файлов
            current_page: Текущая страница (начиная с 0)
            
        Returns:
            InlineKeyboardMarkup: Клавиатура с кнопками файлов и навигации
        """
        total_files = len(files)
        total_pages = (total_files + self.files_per_page - 1) // self.files_per_page
        
        # Вычисляем индексы для текущей страницы
        start_idx = current_page * self.files_per_page
        end_idx = min(start_idx + self.files_per_page, total_files)
        
        # Получаем файлы для текущей страницы
        page_files = files[start_idx:end_idx]
        
        # Создаем кнопки для файлов текущей страницы
        keyboard_buttons = []
        
        for i, file_info in enumerate(page_files, start_idx + 1):
            username = file_info['username']
            size_kb = file_info['size_kb']
            
            # Создаем кнопку для скачивания файла
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"📁 {username} ({size_kb:.1f} KB)",
                    callback_data=f"download_{username}"
                )
            ])
        
        # Добавляем кнопки навигации
        if total_pages > 1:
            navigation_buttons = self._create_navigation_buttons(current_page, total_pages)
            keyboard_buttons.extend(navigation_buttons)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    def create_files_list_text(self, files: List[Dict], current_page: int = 0) -> str:
        """
        Создает текст списка файлов с пагинацией
        
        Args:
            files: Список файлов
            current_page: Текущая страница (начиная с 0)
            
        Returns:
            str: Текст списка файлов
        """
        total_files = len(files)
        total_pages = (total_files + self.files_per_page - 1) // self.files_per_page
        
        # Вычисляем индексы для текущей страницы
        start_idx = current_page * self.files_per_page
        end_idx = min(start_idx + self.files_per_page, total_files)
        
        # Получаем файлы для текущей страницы
        page_files = files[start_idx:end_idx]
        
        # Формируем список пользователей для текущей страницы
        users_list = f"👥 **Список пользователей OpenVPN** (стр. {current_page + 1}/{total_pages}):\n\n"
        
        for i, file_info in enumerate(page_files, start_idx + 1):
            username = file_info['username']
            size_kb = file_info['size_kb']
            users_list += f"{i}. **{username}** ({size_kb:.1f} KB)\n"
        
        users_list += f"\n📊 **Всего пользователей:** {total_files}\n"
        users_list += "💡 **Нажмите на кнопку ниже для скачивания файла:**"
        
        return users_list
    
    def get_page_files(self, files: List[Dict], page: int) -> List[Dict]:
        """
        Получает файлы для указанной страницы
        
        Args:
            files: Список всех файлов
            page: Номер страницы (начиная с 0)
            
        Returns:
            List[Dict]: Файлы для указанной страницы
        """
        start_idx = page * self.files_per_page
        end_idx = min(start_idx + self.files_per_page, len(files))
        return files[start_idx:end_idx]
    
    def get_total_pages(self, files: List[Dict]) -> int:
        """
        Получает общее количество страниц
        
        Args:
            files: Список файлов
            
        Returns:
            int: Общее количество страниц
        """
        return (len(files) + self.files_per_page - 1) // self.files_per_page
    
    def _create_navigation_buttons(self, current_page: int, total_pages: int) -> List[List[InlineKeyboardButton]]:
        """
        Создает кнопки навигации
        
        Args:
            current_page: Текущая страница
            total_pages: Общее количество страниц
            
        Returns:
            List[List[InlineKeyboardButton]]: Кнопки навигации
        """
        navigation_buttons = []
        nav_row = []
        
        # Кнопка "Назад"
        if current_page > 0:
            nav_row.append(InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"page_{current_page - 1}"
            ))
        
        # Информация о странице
        nav_row.append(InlineKeyboardButton(
            text=f"{current_page + 1}/{total_pages}",
            callback_data="page_info"
        ))
        
        # Кнопка "Вперед"
        if current_page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"page_{current_page + 1}"
            ))
        
        navigation_buttons.append(nav_row)
        return navigation_buttons
