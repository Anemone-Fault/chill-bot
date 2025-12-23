"""
Конфигурация бота из переменных окружения
"""
import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# VK Configuration
VK_GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN')
VK_GROUP_ID = int(os.getenv('VK_GROUP_ID', 0))

# Admin IDs (список администраторов)
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# Database
DATABASE_URL = os.getenv('DATABASE_URL')

# Bot Settings
RATE_LIMIT_SECONDS = int(os.getenv('RATE_LIMIT_SECONDS', 2))
MAX_REQUESTS_PER_HOUR = int(os.getenv('MAX_REQUESTS_PER_HOUR', 10))
CONFIRMATION_TIMEOUT_MINUTES = int(os.getenv('CONFIRMATION_TIMEOUT_MINUTES', 5))
STARTING_BALANCE = int(os.getenv('STARTING_BALANCE', 100))
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')

# Validation
if not VK_GROUP_TOKEN:
    raise ValueError("VK_GROUP_TOKEN не установлен в .env файле!")
if not VK_GROUP_ID:
    raise ValueError("VK_GROUP_ID не установлен в .env файле!")
if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS не установлены в .env файле!")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не установлен в .env файле!")