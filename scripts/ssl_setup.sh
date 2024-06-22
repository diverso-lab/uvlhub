#!/bin/bash

while true; do
    echo "Enter your domain (including 'www' and the extension, e.g., www.exampledomain.com):"
    read domain

    echo "Enter your email: "
    read email

    echo "Configured with the domain $domain"
    echo "Configured with the email $email"
    echo ""
    echo "Are you sure the entered information is correct? [y/n]"
    read confirm

    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        break
    else
        echo "Please re-enter the information."
        echo ""
    fi
done

cd .. # go to parent folder

cd docker # go to docker folder

# Create a new configuration file from the template
cp ./nginx/nginx.prod.no-ssl.conf.template ./nginx/nginx.prod.ssl.conf
sed -i "s/{{domain}}/$domain/g" ./nginx/nginx.prod.ssl.conf

# Run Nginx container without SSL to obtain certificates
docker compose -f docker-compose.prod.ssl.yml up -d nginx

# Generate the certificate with Certbot
docker compose -f docker-compose.prod.ssl.yml run certbot certonly --webroot --webroot-path=/var/www -d $domain --email $email --agree-tos --no-eff-email --force-renewal

# Create a new configuration file from the SSL template
cp ./nginx/nginx.prod.ssl.conf.template ./nginx/nginx.prod.ssl.conf
sed -i "s/{{domain}}/$domain/g" ./nginx/nginx.prod.ssl.conf

# Restart Nginx with SSL configuration
docker compose -f docker-compose.prod.ssl.yml down
docker compose -f docker-compose.prod.ssl.yml up -d --build

cd .. # go to parent folder
