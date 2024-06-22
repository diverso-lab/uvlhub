#!/bin/bash

while true; do
    # Prompt for domain and email
    echo "Enter your domain (including 'www' and the extension, e.g., www.exampledomain.com):"
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

cd .. # go to parent folder

# Navigate to the docker folder
cd docker

# Create a new configuration file from the template
cp ./nginx/nginx.prod.ssl.conf.template ./nginx/nginx.prod.ssl.conf

# Replace the placeholder domain in the new configuration file
sed -i "s/{{domain}}/$domain/g" ./nginx/nginx.prod.ssl.conf

# Run Nginx container in dev mode (only to generate SSL)
docker compose -f docker-compose.dev.yml up -d nginx

# Generate the certificate with Certbot
docker compose -f docker-compose.prod.ssl.yml run certbot certonly --webroot --webroot-path=/var/www -d $domain --email $email --agree-tos --no-eff-email --force-renewal

# Configure Nginx to use the new certificate
docker compose -f docker-compose.dev.yml down && docker compose -f docker-compose.prod.ssl.yml up -d --build

cd .. # go to parent folder
