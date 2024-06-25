#!/bin/sh

# Get the current remote URL
REMOTE_URL=$(git remote get-url origin)

# Check if the URL is SSH
if echo "$REMOTE_URL" | grep -q "git@"; then
  # Convertir la URL SSH a HTTPS
  HTTPS_URL=$(echo "$REMOTE_URL" | sed 's/git@/https:\/\//; s/:/\//')
  git remote set-url origin "$HTTPS_URL"
  
  # Pull from the main branch
  git pull origin main
  
  # Restore the original SSH URL
  git remote set-url origin "$REMOTE_URL"
else
  # Pull from the main branch if the URL is already HTTPS
  git pull origin main
fi
