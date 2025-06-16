#!/bin/bash
set -e

PGADMIN_URL="http://localhost:5050"
APP_URL="http://localhost:8080"
DB_HOST="postgres"
DB_PORT="5432"
DB_USER="postgres"
DB_PASS="postgres"
DB_NAME="aviacao"
NOTEBOOK_CONTAINER="bdist-workspace-notebook-1"
JUPYTER_PASSWORD="password"

COMPOSE_FILE="docker-compose..app.yml"

cd bdist-workspace

# Define notebook service blocks as HEREDOCs
notebook_block_vscode="  notebook:
    restart: unless-stopped
    image: ghcr.io/bdist/notebook:2025-02-18
    volumes:
      - ../app:/home/jovyan/app
      - ./data:/home/jovyan/data
      - ./images:/home/jovyan/images
      - ./work:/home/jovyan/work
    environment:
      - JUPYTER_PORT=9999
      - JUPYTER_PASSWORD=\${JUPYTER_PASSWORD}
    ports:
      - 9999:9999
    command: \"start-notebook.sh --NotebookApp.token='\${JUPYTER_PASSWORD}'\"
    networks:
      - bdist-workspace-network"

notebook_block_default="  notebook:
    restart: unless-stopped
    image: ghcr.io/bdist/notebook:2025-02-18
    volumes:
      - ../app:/home/jovyan/app
      - ./data:/home/jovyan/data
      - ./images:/home/jovyan/images
      - ./work:/home/jovyan/work
    environment:
      - JUPYTER_PORT=9999
    ports:
      - 9999:9999
    networks:
      - bdist-workspace-network"

# Function to replace notebook block
replace_notebook_block() {
  local block="$1"
  local file="$2"
  # Find start and end line numbers of the notebook block
  local start=$(grep -n '^  notebook:' "$file" | cut -d: -f1 | head -n1)
  if [[ -z "$start" ]]; then
    echo "notebook block not found in $file"
    exit 1
  fi
  # Find the next service or end of file
  local end=$(awk "NR>$start && /^  [a-zA-Z0-9_-]+:/ {print NR; exit}" "$file")
  if [[ -z "$end" ]]; then
    end=$(wc -l < "$file")
    end=$((end+1))
  fi
  # Write everything before notebook, then the block, then everything after
  {
    head -n $((start-1)) "$file"
    echo "$block"
    tail -n +$end "$file"
  } > "$file.tmp"
  mv "$file.tmp" "$file"
}

if [[ "$1" == "--vscode" ]]; then
  replace_notebook_block "$notebook_block_vscode" "$COMPOSE_FILE"
  SKIP_NOTEBOOK_URL=1
else
  replace_notebook_block "$notebook_block_default" "$COMPOSE_FILE"
  SKIP_NOTEBOOK_URL=0
fi

JUPYTER_PASSWORD=$JUPYTER_PASSWORD docker compose -f $COMPOSE_FILE up -d

echo "---------------------------------------------"
NOTEBOOK_URL=""
if [[ $SKIP_NOTEBOOK_URL -eq 0 ]]; then
  for i in {1..18}; do
      NOTEBOOK_URL=$(docker logs $NOTEBOOK_CONTAINER 2>&1 | grep -oE 'http://127.0.0.1:[0-9]+/(lab\?token|lab/\?token|/\?token)=[a-zA-Z0-9]+' | tail -1 | sed 's/127.0.0.1/localhost/')
      if [ -n "$NOTEBOOK_URL" ]; then
          break
      fi
      sleep 5
  done
fi

if [[ -n "$NOTEBOOK_URL" ]]; then
    echo "Jupyter Notebook: $NOTEBOOK_URL"
else
    echo "Jupyter Notebook: http://localhost:9999/lab"
    echo "Use the password (on vscode or the webpage): $JUPYTER_PASSWORD"
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

# Show available databases
docker exec -it $NOTEBOOK_CONTAINER bash -c "
export PGPASSWORD='$DB_PASS'
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c '\l'
"

echo "Environment is ready. Use the connection info above to connect to the database."

# Open a shell in the notebook container for psql access
echo "Opening a shell in the '$NOTEBOOK_CONTAINER' container for psql access..."
docker exec -it $NOTEBOOK_CONTAINER bash -c "export PGPASSWORD='$DB_PASS'; psql -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME"
