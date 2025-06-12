#!/bin/bash
set -e

PGADMIN_URL="http://localhost:5050"
APP_URL="http://localhost:8080"
DB_HOST="postgres"
DB_PORT="5432"
DB_USER="postgres"
DB_PASS="postgres"
DB_NAME="postgres"
NOTEBOOK_CONTAINER="bdist-workspace-notebook-1"

NEW_DB_USER="postgres"
NEW_DB_PASS="postgres"
NEW_DB_NAME="aviacao"
SCHEMA_PATH="./data/aviacao.sql"

cd bdist-workspace
docker compose -f docker-compose..app.yml up -d

echo "---------------------------------------------"
NOTEBOOK_URL=""
for i in {1..18}; do
    NOTEBOOK_URL=$(docker logs $NOTEBOOK_CONTAINER 2>&1 | grep -oE 'http://127.0.0.1:[0-9]+/(lab\?token|lab/\?token|/\?token)=[a-zA-Z0-9]+' | tail -1 | sed 's/127.0.0.1/localhost/')
    if [ -n "$NOTEBOOK_URL" ]; then
        break
    fi
    sleep 5
done
if [ -n "$NOTEBOOK_URL" ]; then
    echo "Jupyter Notebook: $NOTEBOOK_URL"
else
    echo "Jupyter Notebook: (URL not found after waiting, check container logs with: docker logs $NOTEBOOK_CONTAINER)"
fi
echo "pgAdmin:          $PGADMIN_URL"
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

docker exec -i $NOTEBOOK_CONTAINER bash -c "
export PGPASSWORD='$DB_PASS'
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -w -c \"
SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = '$NEW_DB_USER';
\" | grep -q 1 || psql -h $DB_HOST -U $DB_USER -d $DB_NAME -w -c \"
CREATE USER $NEW_DB_USER WITH PASSWORD '$NEW_DB_PASS';
\"
"

docker exec -i $NOTEBOOK_CONTAINER bash -c "
export PGPASSWORD='$DB_PASS'
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -w -c \"
SELECT 1 FROM pg_catalog.pg_database WHERE datname = '$NEW_DB_NAME';
\" | grep -q 1 || psql -h $DB_HOST -U $DB_USER -d $DB_NAME -w -c \"
CREATE DATABASE $NEW_DB_NAME OWNER $NEW_DB_USER;
\"
"

docker exec -i $NOTEBOOK_CONTAINER bash -c "
export PGPASSWORD='$NEW_DB_PASS'
psql -h $DB_HOST -U $NEW_DB_USER -d $NEW_DB_NAME -w -f /home/jovyan/data/aviacao.sql
"

docker exec -it bdist-workspace-notebook-1 bash -c "
export PGPASSWORD='postgres'
psql -h postgres -U postgres -d postgres -c '\l'
"

echo "Database '$NEW_DB_NAME' created and schema imported."
echo "New database connection info:"
echo "  Host:     $DB_HOST"
echo "  Port:     $DB_PORT"
echo "  User:     $NEW_DB_USER"
echo "  Password: $NEW_DB_PASS"
echo "  Database: $NEW_DB_NAME"

# Open a shell in the notebook container and run psql as the new user
echo "Opening a shell in the '$NOTEBOOK_CONTAINER' container for psql access (as $NEW_DB_USER)..."
docker exec -it $NOTEBOOK_CONTAINER bash -c "export PGPASSWORD='$NEW_DB_PASS'; psql -h $DB_HOST -p $DB_PORT -U $NEW_DB_USER $NEW_DB_NAME"
