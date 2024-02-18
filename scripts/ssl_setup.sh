#!/bin/bash

while true; do
    # Prompt for domain and email
    echo "Enter your domain (including 'www' and '.com' or '.org' or whatever the extension). Example: www.exampledomain.com"
    read domain

    echo "Enter your email: "
    read email

    # Display a summary of the entered data and ask for confirmation
    echo "Configured with the domain $domain"
    echo "Configured with the email $email"
    echo ""
    echo "Are you sure the entered information is correct? [y/n]"
    read confirm

    # If the user confirms, break the loop and continue with the script. Otherwise, repeat the loop.
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        break
    else
        echo "Please re-enter the information."
        echo ""
    fi
done

# Replace the placeholder domain in the configuration file
sed -i "s/www.domain.com/$domain/g" ./nginx/nginx.dev.conf
sed -i "s/www.domain.com/$domain/g" ./nginx/nginx.prod.conf

# Run Nginx container in dev mode (only for generate SSL)
docker compose -f docker-compose.dev.yml up -d nginx

# Generate the certificate with Certbot
docker compose -f docker-compose.prod.yml run certbot certonly --webroot --webroot-path=/var/www -d $domain --email $email --agree-tos --no-eff-email --force-renewal

# Configure Nginx to use the new certificate
docker compose -f docker-compose.dev.yml down && docker compose -f docker-compose.prod.yml up -d --build
