import subprocess
import os
import glob
from typing import List, Dict, Optional, Tuple


class UserService:
    """Сервис для работы с пользователями OpenVPN"""
    
    def __init__(self, ovpn_dir: str = "/root/ovpns", easy_rsa_dir: str = "/etc/openvpn/server/easy-rsa"):
        self.ovpn_dir = ovpn_dir
        self.easy_rsa_dir = easy_rsa_dir
        self.client_common_path = "/etc/openvpn/server/client-common.txt"
    
    def create_user(self, username: str) -> Tuple[bool, str]:
        """
        Создает нового пользователя OpenVPN
        
        Args:
            username: Имя пользователя
            
        Returns:
            Tuple[bool, str]: (успех, сообщение об ошибке или успехе)
        """
        try:
            # Проверяем валидность имени пользователя
            if not self._is_valid_username(username):
                return False, "Имя пользователя может содержать только буквы, цифры, дефисы и подчеркивания!"
            
            # Проверяем, что OpenVPN установлен
            if not self._is_openvpn_installed():
                return False, "OpenVPN не установлен или easy-rsa не найден на хосте"
            
            # Проверяем, что пользователь не существует
            if self._user_exists(username):
                return False, f"Пользователь {username} уже существует"
            
            # Создаем сертификат
            success, message = self._create_certificate(username)
            if not success:
                return False, message
            
            # Создаем .ovpn файл
            success, message = self._create_ovpn_file(username)
            if not success:
                return False, message
            
            return True, f"Пользователь {username} успешно создан!"
            
        except Exception as e:
            return False, f"Ошибка при создании пользователя: {str(e)}"
    
    def get_all_users(self) -> Tuple[bool, List[Dict], str]:
        """
        Получает список всех пользователей
        
        Returns:
            Tuple[bool, List[Dict], str]: (успех, список пользователей, сообщение об ошибке)
        """
        try:
            if not os.path.exists(self.ovpn_dir):
                return False, [], "Директория с .ovpn файлами не найдена!"
            
            # Получаем список всех .ovpn файлов
            ovpn_files = glob.glob(os.path.join(self.ovpn_dir, "*.ovpn"))
            
            if not ovpn_files:
                return True, [], "Список пользователей пуст"
            
            # Сортируем файлы по имени
            ovpn_files.sort()
            
            # Формируем список пользователей
            users = []
            for file_path in ovpn_files:
                filename = os.path.basename(file_path)
                username = filename.replace('.ovpn', '')
                file_size = os.path.getsize(file_path)
                
                users.append({
                    'username': username,
                    'filename': filename,
                    'file_path': file_path,
                    'size_kb': file_size / 1024
                })
            
            return True, users, ""
            
        except Exception as e:
            return False, [], f"Ошибка при получении списка пользователей: {str(e)}"
    
    def get_user_file(self, username: str) -> Tuple[bool, str, str]:
        """
        Получает путь к файлу пользователя
        
        Args:
            username: Имя пользователя
            
        Returns:
            Tuple[bool, str, str]: (успех, путь к файлу, сообщение об ошибке)
        """
        try:
            file_path = os.path.join(self.ovpn_dir, f"{username}.ovpn")
            
            if not os.path.exists(file_path):
                return False, "", f"Файл {username}.ovpn не найден"
            
            return True, file_path, ""
            
        except Exception as e:
            return False, "", f"Ошибка при получении файла: {str(e)}"
    
    def _is_valid_username(self, username: str) -> bool:
        """Проверяет валидность имени пользователя"""
        return username.replace('_', '').replace('-', '').isalnum()
    
    def _is_openvpn_installed(self) -> bool:
        """Проверяет, установлен ли OpenVPN"""
        return os.path.exists(os.path.join(self.easy_rsa_dir, "easyrsa"))
    
    def _user_exists(self, username: str) -> bool:
        """Проверяет, существует ли пользователь"""
        cert_path = os.path.join(self.easy_rsa_dir, "pki", "issued", f"{username}.crt")
        return os.path.exists(cert_path)
    
    def _create_certificate(self, username: str) -> Tuple[bool, str]:
        """Создает сертификат для пользователя"""
        try:
            # Переходим в директорию easy-rsa
            original_cwd = os.getcwd()
            os.chdir(self.easy_rsa_dir)
            
            # Устанавливаем правильные права доступа для pki директории
            subprocess.run(["chmod", "-R", "755", "pki/"], check=True)
            subprocess.run(["chown", "-R", "root:root", "pki/"], check=True)
            
            # Создаем сертификат для пользователя
            result = subprocess.run(
                ["./easyrsa", "--batch", "--days=3650", "build-client-full", username, "nopass"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return False, f"Ошибка при создании сертификата: {result.stderr}"
            
            return True, "Сертификат создан успешно"
            
        except Exception as e:
            return False, f"Ошибка при создании сертификата: {str(e)}"
        finally:
            os.chdir(original_cwd)
    
    def _create_ovpn_file(self, username: str) -> Tuple[bool, str]:
        """Создает .ovpn файл для пользователя"""
        try:
            # Создаем директорию, если она не существует
            os.makedirs(self.ovpn_dir, exist_ok=True)
            
            if not os.path.exists(self.client_common_path):
                return False, "Файл client-common.txt не найден"
            
            # Создаем .ovpn файл
            ovpn_file_path = os.path.join(self.ovpn_dir, f"{username}.ovpn")
            inline_file_path = os.path.join(self.easy_rsa_dir, "pki", "inline", "private", f"{username}.inline")
            
            with open(ovpn_file_path, 'w') as ovpn_file:
                # Добавляем содержимое client-common.txt
                with open(self.client_common_path, 'r') as common_file:
                    for line in common_file:
                        if not line.startswith('#'):
                            ovpn_file.write(line)
                
                # Добавляем inline содержимое
                if os.path.exists(inline_file_path):
                    with open(inline_file_path, 'r') as inline_file:
                        ovpn_file.write(inline_file.read())
            
            return True, f"Файл {username}.ovpn создан успешно"
            
        except Exception as e:
            return False, f"Ошибка при создании .ovpn файла: {str(e)}"
