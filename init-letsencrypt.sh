#!/usr/bin/env bash
# Первичный выпуск TLS-сертификата Let's Encrypt для прод-стека.
# Запускать ОДИН РАЗ на сервере после того, как DNS домена указывает на этот хост
# и стек поднят (docker compose ... up -d). Дальше certbot-контейнер продлевает сам.
#
# Решает проблему «курица-яйцо»: nginx с ssl-конфигом не стартует без серта, а
# серт не выпустить без живого nginx. Поэтому: ставим временный самоподписанный
# серт → поднимаем nginx → удаляем заглушку → выпускаем настоящий серт → reload.
set -euo pipefail

domains=(repetitor-diary.ru www.repetitor-diary.ru)
email="frolovav01@gmail.com"          # для уведомлений Let's Encrypt о продлении
staging=0                              # 1 — тестовый CA (не упереться в лимиты при отладке)

compose="docker compose -f docker-compose.prod.yml --env-file .env"
certbot_path="/etc/letsencrypt"
webroot="/var/www/certbot"
live="$certbot_path/live/${domains[0]}"

# Хелпер: выполнить команду внутри одноразового certbot-контейнера на тех же томах.
certbot_run() {
  $compose run --rm --entrypoint "$1" certbot
}

echo "### Скачиваем рекомендованные TLS-параметры ..."
# В образе certbot/certbot нет curl — тянем busybox-wget'ом.
certbot_run "sh -c 'wget -qO $certbot_path/options-ssl-nginx.conf https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf && wget -qO $certbot_path/ssl-dhparams.pem https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem'"

echo "### Временный самоподписанный серт для ${domains[0]} ..."
certbot_run "sh -c 'mkdir -p $live && openssl req -x509 -nodes -newkey rsa:2048 -days 1 -keyout $live/privkey.pem -out $live/fullchain.pem -subj \"/CN=localhost\"'"

echo "### Поднимаем nginx (frontend) ..."
$compose up -d frontend

echo "### Удаляем заглушку и выпускаем настоящий серт ..."
certbot_run "sh -c 'rm -rf $certbot_path/live/${domains[0]} $certbot_path/archive/${domains[0]} $certbot_path/renewal/${domains[0]}.conf'"

domain_args=""
for d in "${domains[@]}"; do domain_args="$domain_args -d $d"; done
staging_arg=""; [ "$staging" != "0" ] && staging_arg="--staging"

certbot_run "certbot certonly --webroot -w $webroot $staging_arg $domain_args --email $email --rsa-key-size 4096 --agree-tos --no-eff-email --force-renewal"

echo "### Перечитываем конфиг nginx ..."
$compose exec frontend nginx -s reload

echo "### Готово. Запускаем certbot-демон автопродления ..."
$compose up -d certbot
