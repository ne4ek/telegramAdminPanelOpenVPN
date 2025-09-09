#!/bin/bash

# Скрипт для автоматического добавления пользователя OpenVPN
# Использование: ./add_user.sh username

if [ $# -eq 0 ]; then
    echo "Ошибка: Укажите имя пользователя"
    echo "Использование: $0 username"
    exit 1
fi

USERNAME="$1"

# Проверяем, что OpenVPN установлен на хосте
if [ ! -f "/etc/openvpn/server/easy-rsa/easyrsa" ]; then
    echo "Ошибка: OpenVPN не установлен или easy-rsa не найден на хосте"
    echo "Убедитесь, что OpenVPN установлен на основной системе"
    exit 1
fi

# Проверяем, что пользователь не существует
if [ -e "/etc/openvpn/server/easy-rsa/pki/issued/${USERNAME}.crt" ]; then
    echo "Ошибка: Пользователь $USERNAME уже существует"
    exit 1
fi

# Переходим в директорию easy-rsa
cd /etc/openvpn/server/easy-rsa/

# Создаем сертификат для пользователя
echo "Создаю сертификат для пользователя: $USERNAME"
./easyrsa --batch --days=3650 build-client-full "$USERNAME" nopass

if [ $? -eq 0 ]; then
    # Создаем .ovpn файл в директории /root/ovpns
    OVPN_DIR="/root/ovpns"
    if [ -f "/etc/openvpn/server/client-common.txt" ]; then
        echo "Создаю конфигурационный файл..."
        # Создаем директорию, если она не существует
        mkdir -p "$OVPN_DIR"
        grep -vh '^#' /etc/openvpn/server/client-common.txt /etc/openvpn/server/easy-rsa/pki/inline/private/"$USERNAME".inline > "$OVPN_DIR"/"$USERNAME".ovpn
        echo "✅ Пользователь $USERNAME успешно создан!"
        echo "📁 Файл конфигурации: $OVPN_DIR/$USERNAME.ovpn"
    else
        echo "⚠️  Пользователь создан, но файл client-common.txt не найден"
        echo "📁 Сертификаты созданы в: /etc/openvpn/server/easy-rsa/pki/"
    fi
else
    echo "❌ Ошибка при создании сертификата для пользователя $USERNAME"
    exit 1
fi
