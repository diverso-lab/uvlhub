#!/bin/bash

# ---------------------------------------------------------------------------
# Creative Commons CC BY 4.0 - David Romero - Diverso Lab
# ---------------------------------------------------------------------------
# This script is licensed under the Creative Commons Attribution 4.0 
# International License. You are free to share and adapt the material 
# as long as appropriate credit is given, a link to the license is provided, 
# and you indicate if changes were made.
#
# For more details, visit:
# https://creativecommons.org/licenses/by/4.0/
# ---------------------------------------------------------------------------


read -p "Are you sure you want to stop all containers? (y/n) " stop_containers
if [ "$stop_containers" = "y" ]; then
    echo "Stopping all containers..."
    docker stop $(docker ps -aq)
else
    echo "Skipping stopping containers."
fi

read -p "Are you sure you want to remove all containers? (y/n) " remove_containers
if [ "$remove_containers" = "y" ]; then
    echo "Removing all containers..."
    docker rm $(docker ps -aq)
else
    echo "Skipping removing containers."
fi

read -p "Are you sure you want to remove all volumes? (y/n) " remove_volumes
if [ "$remove_volumes" = "y" ]; then
    echo "Removing all volumes..."
    docker volume rm $(docker volume ls -q)
else
    echo "Skipping removing volumes."
fi

read -p "Are you sure you want to remove all images? (y/n) " remove_images
if [ "$remove_images" = "y" ]; then
    echo "Removing all images..."
    docker rmi $(docker images -q)
else
    echo "Skipping removing images."
fi

echo "All actions have been completed."
