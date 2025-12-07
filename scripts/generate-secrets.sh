#!/bin/bash

echo "# Secrets générés automatiquement" > .env.secrets
echo "DB_PASSWORD=$(openssl rand -base64 32)" >> .env.secrets
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env.secrets

echo "✅ Secrets générés dans .env.secrets"
echo "⚠️  Copier dans .env et SUPPRIMER .env.secrets"
