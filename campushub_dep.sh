#!/bin/bash

# ============================================
# КОНФИГУРАЦИЯ
# ============================================
SSH_HOST="62.169.26.93"
SSH_USER="kril"
SSH_PORT="22"
REMOTE_PATH="/opt/campushub"
LOCAL_PATH="$(pwd)"
SSH_KEY="$HOME/.ssh/id_ed25519_campushub"


# ПАРОЛЬ ПОЛЬЗОВАТЕЛЯ (укажите свой)
USER_PASSWORD="Kril1966"

VENV_NAME="venv"
BOT_SCRIPT="run.py"
REQUIREMENTS_FILE="requirements.txt"
ENV_VPS_FILE=".env_vps"
SERVICE_NAME="campushub"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Функция для выполнения команд с sudo через передачу пароля
sudo_cmd() {
    echo "$USER_PASSWORD" | ssh -p $SSH_PORT -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" "sudo -S bash -c '$1' 2>/dev/null"
}

# Функция для выполнения команд с sudo и выводом результата
sudo_cmd_verbose() {
    echo "$USER_PASSWORD" | ssh -p $SSH_PORT -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" "sudo -S bash -c '$1'"
}

echo -e "\n${GREEN}🚀 Деплой бота${NC}"
echo "========================================="
echo "Хост: $SSH_HOST"
echo "Пользователь: $SSH_USER"
echo "Путь: $REMOTE_PATH"
echo "========================================="

if [ ! -f "$SSH_KEY" ]; then
    log_error "SSH ключ не найден: $SSH_KEY"
    exit 1
fi

# ============================================
# 1. ПРОВЕРКА SSH
# ============================================
log_info "Проверка SSH..."
if ! ssh -q -p $SSH_PORT -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" "exit"; then
    log_error "SSH не работает"
    exit 1
fi
log_success "SSH OK"

# ============================================
# 2. ПРОВЕРКА ПАРОЛЯ
# ============================================
log_info "Проверка sudo пароля..."
if ! echo "$USER_PASSWORD" | ssh -p $SSH_PORT -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" "sudo -S true 2>/dev/null"; then
    log_error "❌ Неправильный пароль или sudo недоступен!"
    log_info "Исправьте USER_PASSWORD в скрипте"
    exit 1
fi
log_success "Пароль правильный"

# ============================================
# 3. ПОДГОТОВКА СЕРВЕРА
# ============================================
log_info "Подготовка сервера..."
sudo_cmd "rm -rf $REMOTE_PATH && mkdir -p $REMOTE_PATH && mkdir -p $REMOTE_PATH/logs && chown -R $SSH_USER:$SSH_USER $REMOTE_PATH && chmod -R 755 $REMOTE_PATH"
log_success "Директории созданы"

# ============================================
# 4. КОПИРОВАНИЕ ФАЙЛОВ
# ============================================
log_info "Копирование файлов..."

if [ ! -f "$LOCAL_PATH/$BOT_SCRIPT" ]; then
    log_error "Файл $BOT_SCRIPT не найден!"
    exit 1
fi

rsync -avz -e "ssh -p $SSH_PORT -i $SSH_KEY" \
    --exclude='.env' \
    --exclude='.env_vps' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='logs/' \
    --exclude='.DS_Store' \
    --exclude='.idea' \
    --exclude='.vscode' \
    --delete \
    ./ "$SSH_USER@$SSH_HOST:$REMOTE_PATH/"

if [ $? -ne 0 ]; then
    log_error "Ошибка rsync"
    exit 1
fi
log_success "Файлы скопированы"

# ============================================
# 5. КОПИРОВАНИЕ .ENV
# ============================================
log_info "Копирование .env..."
if [ -f "$LOCAL_PATH/$ENV_VPS_FILE" ]; then
    scp -P $SSH_PORT -i "$SSH_KEY" "$LOCAL_PATH/$ENV_VPS_FILE" "$SSH_USER@$SSH_HOST:$REMOTE_PATH/.env"
    sudo_cmd "chmod 600 $REMOTE_PATH/.env"
    log_success ".env создан"
else
    log_error ".env_vps не найден!"
    exit 1
fi

# ============================================
# 6. НАСТРОЙКА БАЗЫ ДАННЫХ
# ============================================
#log_info "Настройка базы данных..."
#ssh -p $SSH_PORT -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" "
#    sudo -u postgres psql -c \"CREATE USER campushub_user WITH PASSWORD 'campushub_pass_2024';\" 2>/dev/null || true
#    sudo -u postgres psql -c \"DROP DATABASE IF EXISTS campushub;\" 2>/dev/null || true
#    sudo -u postgres psql -c \"CREATE DATABASE campushub OWNER campushub_user;\"
#    cd $REMOTE_PATH
#    sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql://campushub_user:campushub_pass_2024@localhost:5432/campushub|' .env
#    echo '✅ База данных настроена'
#"

# ============================================
# 7. УСТАНОВКА ЗАВИСИМОСТЕЙ
# ============================================
log_info "Установка зависимостей..."
ssh -p $SSH_PORT -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" "
    cd $REMOTE_PATH

    rm -rf $VENV_NAME
    python3 -m venv $VENV_NAME
    source $VENV_NAME/bin/activate
    pip install --upgrade pip

    if [ -f '$REQUIREMENTS_FILE' ]; then
        echo '📦 Установка из requirements.txt...'
        pip install -r $REQUIREMENTS_FILE
    else
        echo '⚠️ requirements.txt не найден, устанавливаю базовые пакеты...'
        pip install aiogram==3.4.1 pydantic==2.5.3 pydantic-settings==2.1.0 python-dotenv==1.0.0 aiohttp==3.9.0 psycopg2-binary==2.9.9
    fi

    echo ''
    echo '🔍 Проверка установки:'
    pip list | grep -E 'aiogram|pydantic|dotenv|aiohttp|psycopg'

    echo ''
    echo '🔍 Проверка импорта:'
    python3 -c 'import aiogram; print(\"✅ aiogram OK\")' 2>/dev/null || echo '❌ aiogram НЕ УСТАНОВЛЕН'
    python3 -c 'from pydantic_settings import BaseSettings; print(\"✅ pydantic_settings OK\")' 2>/dev/null || echo '❌ pydantic_settings НЕ УСТАНОВЛЕН'

    echo '✅ Зависимости установлены'
"

# ============================================
# 8. СОЗДАНИЕ SYSTEMD СЛУЖБЫ (С ПЕРЕДАЧЕЙ ПАРОЛЯ)
# ============================================
log_info "Создание systemd службы..."

# Создаем файл службы
sudo_cmd_verbose "tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << 'EOF'
[Unit]
Description=Campushub Bot
After=network.target postgresql.service

[Service]
Type=simple
User=$SSH_USER
WorkingDirectory=$REMOTE_PATH
Environment=\"PATH=$REMOTE_PATH/$VENV_NAME/bin:/usr/local/bin:/usr/bin:/bin\"
ExecStart=$REMOTE_PATH/$VENV_NAME/bin/python3 $REMOTE_PATH/$BOT_SCRIPT
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF"

# Активируем и запускаем службу
sudo_cmd_verbose "systemctl daemon-reload && systemctl enable $SERVICE_NAME && systemctl start $SERVICE_NAME"

log_success "Служба создана"

# ============================================
# 9. ПРОВЕРКА СЛУЖБЫ
# ============================================
log_info "Проверка службы..."
sudo_cmd_verbose "systemctl status $SERVICE_NAME --no-pager" || log_warn "⚠️ Служба не запущена"

echo ""
log_info "Последние логи..."
sudo_cmd_verbose "journalctl -u $SERVICE_NAME -n 20 --no-pager" 2>/dev/null || echo "Логов пока нет"

# ============================================
# 10. ЗАВЕРШЕНИЕ
# ============================================
echo -e "\n${GREEN}✅ Деплой завершен!${NC}"
echo "========================================="
echo "📁 Путь: $REMOTE_PATH"
echo "📋 Логи: echo '$USER_PASSWORD' | sudo -S journalctl -u $SERVICE_NAME -f"
echo ""
echo "📌 Команды управления:"
echo "  echo '$USER_PASSWORD' | sudo -S systemctl status $SERVICE_NAME"
echo "  echo '$USER_PASSWORD' | sudo -S systemctl restart $SERVICE_NAME"
echo "  echo '$USER_PASSWORD' | sudo -S journalctl -u $SERVICE_NAME -f"
echo "========================================="