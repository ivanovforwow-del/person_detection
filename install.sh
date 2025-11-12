#!/bin/bash

# Скрипт для быстрой установки микросервиса детекции людей

set -e  # Прекращаем выполнение при ошибке

echo "Начинается установка микросервиса детекции людей..."

# Проверяем, установлен ли Python
if ! command -v python3 &> /dev/null; then
    echo "Ошибка: Python3 не найден. Установите Python3 перед продолжением."
    exit 1
fi

# Проверяем, установлен ли pip
if ! command -v pip3 &> /dev/null; then
    echo "pip3 не найден. Пытаемся установить..."
    python3 -m ensurepip --upgrade
fi

# Устанавливаем зависимости
echo "Устанавливаем зависимости из requirements.txt..."
pip3 install -r requirements.txt

# Проверяем, установлен ли virtualenv
if ! python3 -m venv --help &> /dev/null; then
    echo "Устанавливаем virtualenv..."
    pip3 install virtualenv
fi

# Создаем виртуальное окружение
echo "Создаем виртуальное окружение..."
python3 -m venv venv

# Активируем виртуальное окружение и устанавливаем зависимости
echo "Активируем виртуальное окружение и устанавливаем зависимости..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Установка завершена успешно!"
echo "Для запуска микросервиса выполните:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Или для установки в систему как пакет:"
echo "  pip install -e ."