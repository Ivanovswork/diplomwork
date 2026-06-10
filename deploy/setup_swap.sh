#!/bin/bash

# Скрипт настройки swap файла для сервера с 1 ГБ RAM
# Запускать от root

echo "=== Настройка swap файла ==="

# Проверка, есть ли уже swap
if [ -f /swapfile ]; then
    echo "Swap файл уже существует!"
    swapon --show
    exit 0
fi

# Создание swap файла 2 ГБ
echo "Создание swap файла 2 ГБ..."
fallocate -l 2G /swapfile

# Установка правильных прав
chmod 600 /swapfile

# Инициализация swap
mkswap /swapfile

# Включение swap
swapon /swapfile

# Проверка
echo ""
echo "=== Статус swap ==="
swapon --show
free -h

# Добавление в fstab для постоянного включения
echo ""
echo "Добавление в /etc/fstab..."
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Настройка swappiness (меньше = реже использовать swap)
sysctl vm.swappiness=10
echo 'vm.swappiness=10' >> /etc/sysctl.conf

echo ""
echo "=== Swap настроен успешно! ==="
