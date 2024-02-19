#!/bin/sh

until mysql -h db -P 3306 -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -e 'SELECT 1' &> /dev/null
do
  echo "MySQL is unavailable - sleeping"
  sleep 1
done

echo "MySQL is up - executing command"
exec "$@"