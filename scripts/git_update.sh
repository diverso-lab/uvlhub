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

# Get the current remote URL
REMOTE_URL=$(git remote get-url origin) 

if [ -z "$REMOTE_URL" ]; then 
  echo "No remote URL found for 'origin'. Please configure the remote repository." 
  exit 1 
fi 

echo "Original remote URL: $REMOTE_URL"

# Check if the URL is SSH
if echo "$REMOTE_URL" | grep -q "git@"; then

  # Convert SSH URL to HTTPS
  USER_HOST=$(echo "$REMOTE_URL" | cut -d'@' -f2 | cut -d':' -f1)
  REPO_PATH=$(echo "$REMOTE_URL" | cut -d':' -f2)
  HTTPS_URL="https://$USER_HOST/$REPO_PATH"
  echo "Converted SSH URL to HTTPS: $HTTPS_URL"

  # Set the new HTTPS URL
  git remote set-url origin "$HTTPS_URL"

  # Verify the new remote URL
  NEW_REMOTE_URL=$(git remote get-url origin) 
  echo "New remote URL: $NEW_REMOTE_URL"

  # Pull from the main branch
  git pull origin main
  echo "Pulled from main from: $NEW_REMOTE_URL"

  # Restore the original SSH URL
  git remote set-url origin "$REMOTE_URL"

else

  echo "The URL is already HTTPS"

  # Pull from the main branch if the URL is already HTTPS
  git pull origin main
  echo "Pulled from main from: $REMOTE_URL"

fi
