#!/bin/bash
cd .. # go to parent folder
docker compose -f docker-compose.prod.yml run certbot renew --webroot --webroot-path=/var/www
