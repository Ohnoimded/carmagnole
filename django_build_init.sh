#!/bin/bash

# Change directory to your Django project directory
cd /carmagnole



# Run database migrations and checks
python manage.py check
python manage.py makemigrations utils
python manage.py makemigrations authenticate
python manage.py makemigrations
python manage.py migrate authenticate
python manage.py migrate utils
python manage.py migrate

# python manage.py sqlmigrate utils 0003

# Add a cron job to run every minute (adjust paths and commands as needed)
echo "*/4 * * * * /usr/local/bin/python /carmagnole/manage.py run_etl >> /var/log/cron.log 2>&1" | crontab -
# echo "*/2 */336 * * * /usr/local/bin/python /carmagnole/manage.py backup_logs >> /var/log/cron.log 2>&1" | crontab -

# Start the cron daemon for news etl 
# service cron restart
service cron start
# crond 


##########################

# # Experimental daemon for fetching and loading market data

# chmod +x /carmagnole/market_data/management/commands/market_fetch_live.py

# cp /carmagnole/market_data/data_market_fetch_daemon.service /etc/systemd/system/

# systemctl daemon-reload

# systemctl start data_market_fetch_daemon
# systemctl enable data_market_fetch_daemon

# echo "0 0 * * 6 /usr/bin/systemctl stop data_market_fetch_daemon.service>> /var/log/cron.log 2>&1" | crontab -
# echo "0 0 * * 1 /usr/bin/systemctl start data_market_fetch_daemon.service >> /var/log/cron.log 2>&1" | crontab -

# ##########################

#start memcached with custom user
# id -u memcacheduser &>/dev/null || useradd -m -d /home/memcacheduser -s /bin/bash memcacheduser
# su - memcacheduser -s /bin/sh -c "memcached -m 48 -u memcacheduser" &


## Alpine
#start memcached with custom user
# id -u memcacheduser &>/dev/null || adduser -D -h /home/memcacheduser memcacheduser
# su -s /bin/sh -c "memcached -m 48 -u memcacheduser" memcacheduser &

# Start the Django development server
# python manage.py runserver 0.0.0.0:8000
# gunicorn --config gunicorn_config.py carmagnole.wsgi:application
# uvicorn carmagnole.asgi:application --host 0.0.0.0 --port 8000 --workers 2 --timeout-keep-alive 15   --limit-concurrency 500
# daphne -b 0.0.0.0 -p 8000 carmagnole.asgi:application  --workers 7 --threads 2
# --ssl-keyfile=./certificates/server.key --ssl-certfile=./certificates/server.crt 
# hypercorn carmagnole.asgi:application \
#   --bind 0.0.0.0:8000 \
#   --http h2
# #   --certfile ./certificates/server.crt \
# #   --keyfile ./certificates/server.key \


# hypercorn --certfile ./certificates/carmagnole.crt --keyfile ./certificates/carmagnole.key \
#             --bind 0.0.0.0:8000 \
#             --log-level debug \
#             --reload \
#             carmagnole.asgi:application \
#             --read-timeout 120 \
#             -w 1

uvicorn carmagnole.asgi:application  --host 0.0.0.0 --port 8000 
# \
    # --ssl-keyfile ./certificates/carmagnole.key \
    # --ssl-certfile ./certificates/carmagnole.crt \
    # --log-level debug 
    # --timeout-keep-alive 120
