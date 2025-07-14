#!/bin/bash
set -e

PGADMIN_URL="http://localhost:5050"
APP_URL="http://localhost:8080"
DB_HOST="postgres"
DB_PORT="5432"
DB_USER="postgres"
DB_PASS="postgres"
DB_NAME="aviacao"
NOTEBOOK_CONTAINER="bd-ist-notebook-1"
JUPYTER_PASSWORD="password"

COMPOSE_FILE="docker-compose.yml"

JUPYTER_PASSWORD=$JUPYTER_PASSWORD docker compose -f $COMPOSE_FILE up -d

echo "---------------------------------------------"

echo "Jupyter Notebook: http://localhost:9999/lab"
echo "Use the password (on vscode or the webpage): $JUPYTER_PASSWORD"

echo "App:              $APP_URL"
echo ""
echo "Database connection info:"
echo "  Host:     $DB_HOST"
echo "  Port:     $DB_PORT"
echo "  User:     $DB_USER"
echo "  Password: $DB_PASS"
echo "  Database: $DB_NAME"
echo "---------------------------------------------"
echo ""

# Show available databases
docker exec -it $NOTEBOOK_CONTAINER bash -c "
export PGPASSWORD='$DB_PASS'
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c '\l'
"

echo "Environment is ready. Use the connection info above to connect to the database."

# Open a shell in the notebook container for psql access
echo "Opening a shell in the '$NOTEBOOK_CONTAINER' container for psql access..."
docker exec -it $NOTEBOOK_CONTAINER bash -c "export PGPASSWORD='$DB_PASS'; psql -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME"
