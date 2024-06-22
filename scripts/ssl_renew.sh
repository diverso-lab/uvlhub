#!/bin/bash

cd .. # go to parent folder

cd docker # go to docker folder

docker compose -f docker-compose.prod.ssl.yml run certbot renew --webroot --webroot-path=/var/www
