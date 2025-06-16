#!/usr/bin/python3
"""
Flask API for listing airports and flights,
ticket purchase, and check-in operations.
"""
from logging.config import dictConfig
import re
import time
import random
import os
from flask import Flask, jsonify, request, abort
from psycopg.rows import dict_row
import psycopg
import psycopg_pool

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": (
                    "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)s - "
                    "%(funcName)20s(): %(message)s"
                ),
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

app = Flask(__name__)
app.config.from_prefixed_env()
app.json.sort_keys = False
log = app.logger

# In this case we don't have the env variable defined, so the default
# connection string is used.
DATABASE_URL = os.environ.get("DATABASE_URL",
    "postgres://postgres:postgres@postgres/aviacao")

# Setup DB connection
db_pool = psycopg_pool.ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=10,
    timeout=5
)

# Rate Limit API endpoints
RATE_LIMIT = 100     # num requests
TIME_INTERVAL = 60  # per num seconds
rate_limit = {}

# Custom Exception Classes
class ApiError(Exception):
    """Flask API DB request exceptions."""
    def __init__(self, code, message, error = None):
        super().__init__(message)
        self.error = error
        self.code = code if code else 500
        self.description = message or {}

# Speciallization of API Exception
class NotFoundError(ApiError):
    """Not found errors."""
    def __init__(self, message):
        super().__init__(404, message, error="Not Found")

class ConflictError(ApiError):
    """Conflict errors."""
    def __init__(self, message):
        super().__init__(409, message, error="Conflict")

class BadRequestError(ApiError):
    """Bad request errors."""
    def __init__(self, message):
        super().__init__(400, message, error="Bad Request")

# Database Connection pool helpers
def get_db_connection():
    """Get a db connection from the pool."""
    return db_pool.getconn()

def put_db_connection(connnection):
    """Release db connection into the pool."""
    return db_pool.putconn(connnection)

# Rate Limiting Helper
def is_rate_limited(ip):
    """Check if client is above the limit of requests for a time interval."""
    now = time.time()
    timestamps = [t for t in rate_limit.get(ip, []) if t > now - TIME_INTERVAL]
    if len(timestamps) >= RATE_LIMIT:
        return True
    timestamps.append(now)
    rate_limit[ip] = timestamps
    return False

# Aux functions for API Endpoints
def get_data_all_airports():
    """List all the airports available on the database."""
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT nome, cidade FROM aeroporto")
            return cursor.fetchall()
    except psycopg.Error as e:
        raise ApiError("Erro ao listar todos os aeroportos.",
            {"detalhes": str(e)}) from e
    finally:
        put_db_connection(db_connection)

def airport_exists(cursor, airport_code):
    """Check if an airport exists by its code."""
    cursor.execute("SELECT EXISTS(SELECT 1 FROM aeroporto WHERE codigo = %s)",
        (airport_code,))
    return cursor.fetchone()["exists"]

def get_data_next_departure_flights(departure_airport):
    """Gets all flights departing the selected airport in the next 12 hours."""
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(row_factory=dict_row) as cursor:
            if not airport_exists(cursor, departure_airport):
                raise NotFoundError(f"""Aeroporto de partida ({departure_airport})
                    não encontrado.""")
            cursor.execute("""SELECT no_serie, hora_partida, chegada FROM voo
                WHERE partida = %s AND hora_partida
                BETWEEN NOW() AND NOW() + INTERVAL '12 hours'""",
                (departure_airport,))
            data = cursor.fetchall()
            if not data:
                raise NotFoundError(f"""Nenhum voo encontrado para o aeroporto
                    {departure_airport} nas próximas 12 horas.""")
            return data
    except psycopg.Error as error:
        raise ApiError("Erro ao obter os voos que partem nas próximas 12 horas.",
            {"detalhes": str(error)}) from error
    finally:
        put_db_connection(db_connection)

def get_available_flights(departure_airport, arrival_airport):
    """Lists the next 3 flights with available capacity."""
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(row_factory=dict_row) as cursor:
            if not airport_exists(cursor, departure_airport):
                raise NotFoundError(f"Aeroporto de partida "
                    f"({departure_airport}) não encontrado.")
            if not airport_exists(cursor, arrival_airport):
                raise NotFoundError(f"Aeroporto de chegada "
                    f"({arrival_airport}) não encontrado.")
            # a = assentos por avião, b = bilhetes por voo
            cursor.execute("""
                SELECT v.no_serie, v.hora_partida
                FROM voo v
                JOIN (
                    SELECT no_serie, COUNT(*) AS total_assentos
                    FROM assento
                    GROUP BY no_serie
                ) a ON v.no_serie = a.no_serie
                LEFT JOIN (
                    SELECT voo_id, COUNT(*) AS vendidos
                    FROM bilhete
                    GROUP BY voo_id
                ) b ON v.id = b.voo_id
                WHERE v.partida = %s
                  AND v.chegada = %s
                  AND v.hora_partida > NOW()
                  AND COALESCE(b.vendidos, 0) < a.total_assentos
                ORDER BY v.hora_partida
                LIMIT 3
            """, (departure_airport, arrival_airport))
            data = cursor.fetchall()
            if not data:
                raise NotFoundError(f"Nenhum voo com lugares disponíveis "
                    f"encontrado para a rota desejada. "
                    f"Origem: {departure_airport}, Destino: {arrival_airport}.")
            return data
    except psycopg.Error as error:
        raise ApiError("Erro ao obter os voos disponíveis.",
            {"detalhes": str(error)}) from error
    finally:
        put_db_connection(db_connection)

def get_available_seats(cursor, flight_id, prim_classe):
    """Returns the number of available seats for a given flight and class."""
    cursor.execute("""
        SELECT COUNT(*) AS no_assentos
        FROM assento
        WHERE no_serie = (SELECT no_serie FROM voo WHERE id = %s)
        AND prim_classe = %s
        AND lugar NOT IN (
            SELECT lugar FROM bilhete
            WHERE voo_id = %s
        )
    """, (flight_id, prim_classe, flight_id))
    return cursor.fetchone()["no_assentos"]

def get_ticket_price(cursor, flight_id, prim_classe):
    """Get the ticket price for a given flight and class.
    If not found, try the other class and adjust price by 40%.
    If still not found, generate a random price.
    """
    cursor.execute( # Check existing price for the specified class and flight
        """SELECT preco FROM bilhete WHERE voo_id = %s AND prim_classe = %s
        AND preco IS NOT NULL LIMIT 1""",
        (flight_id, prim_classe)
    )
    row = cursor.fetchone()
    if row: return row["preco"]

    # If no price is found check existing price for the other class
    cursor.execute(
        """SELECT preco FROM bilhete WHERE voo_id = %s AND prim_classe = %s
        AND preco IS NOT NULL LIMIT 1""",
        (flight_id, not prim_classe)
    )
    row = cursor.fetchone()
    # If still no price is found, generate random price.
    if not row: return round(random.uniform(80, 350), 2)
    # If a price is found, adjust it based on the class
    # 40% more for first class, 40% less for second class
    alt_price = row["preco"]
    return round(alt_price * 1.4, 2) if prim_classe else round(alt_price * 0.6, 2)

def register_sale(flight_id, nif, tickets_data):
    """Buy tickets for a flight, ensuring availability before selling."""
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(row_factory=dict_row) as cursor:
            # Verify the flight exists
            cursor.execute("SELECT EXISTS(SELECT 1 FROM voo WHERE id = %s)",
                (flight_id,))
            if not cursor.fetchone()["exists"]:
                raise NotFoundError(f"Voo ({flight_id}) não encontrado.")
            with db_connection.transaction():
                cursor.execute("""INSERT INTO venda (nif_cliente, balcao, hora)
                    VALUES (%s, NULL, NOW()) RETURNING codigo_reserva""", (nif,))
                reservation_code = cursor.fetchone()["codigo_reserva"]
                for ticket in tickets_data:
                    if not isinstance(ticket, dict) or \
                        "nome" not in ticket or \
                        "prim_classe" not in ticket:
                        raise BadRequestError("Dados de bilhete inválidos." \
                        "É necessário fornecer o nome do passageiro e a" \
                        "classe (prim_classe) do bilhete.")
                    available = get_available_seats(cursor,
                        flight_id, ticket["prim_classe"])
                    if available == 0:
                        raise ConflictError(
                            f"Não há mais bilhetes de "
                            f"{'primeira' 
                            if str(ticket['prim_classe']).lower() == 'true'
                            else 'segunda'} "
                            f"classe disponíveis para o voo {flight_id}."
                        )
                    price_row = get_ticket_price(cursor, flight_id,
                        ticket["prim_classe"])
                    cursor.execute(
                        """INSERT INTO bilhete (voo_id, codigo_reserva,
                        nome_passegeiro, preco, prim_classe, lugar, no_serie)
                        VALUES (%s, %s, %s, %s, %s, NULL, NULL)""",
                        (flight_id, reservation_code, ticket["nome"],
                            price_row, ticket["prim_classe"]))
    except ApiError:
        db_connection.rollback()
        raise
    except (psycopg.Error, Exception) as e:
        db_connection.rollback()
        raise ApiError("Erro ao comprar bilhetes.", {"detalhes": str(e)}) from e
    finally:
        put_db_connection(db_connection)

def register_check_in(bilhete_id):
    """Checks in the passenger, assigns a seat to the ticket in the correct class."""
    db_connection = get_db_connection()
    try:
        with db_connection.transaction():
            with db_connection.cursor(row_factory=dict_row) as db_query:
                db_query.execute("""SELECT voo_id, prim_classe, lugar, no_serie
                    FROM bilhete WHERE id = %s
                    FOR UPDATE NOWAIT""", (bilhete_id,))
                bilhete = db_query.fetchone()
                if not bilhete:
                    raise NotFoundError(f"Bilhete não encontrado "
                        f"Bilhete ID: {bilhete_id}.")
                # Check if passenger has already checked in
                if bilhete["lugar"] is not None and bilhete["no_serie"] is not None:
                    raise ConflictError(
                        f"Check-in já realizado para este bilhete. "
                        f"Bilhete ID: {bilhete_id}.")
                db_query.execute("SELECT no_serie FROM voo WHERE id = %s",
                    (bilhete["voo_id"],))
                voo = db_query.fetchone()
                if not voo:
                    raise NotFoundError(f"Voo {bilhete['voo_id']} não encontrado")
                db_query.execute("""SELECT lugar FROM assento WHERE
                    no_serie = %s AND prim_classe = %s AND (lugar, no_serie)
                    NOT IN (SELECT lugar FROM bilhete
                    WHERE voo_id = %s) FOR UPDATE SKIP LOCKED LIMIT 1""",
                    (voo["no_serie"], bilhete["prim_classe"], bilhete["voo_id"]))
                assento = db_query.fetchone()
                if not assento:
                    raise ConflictError(
                        f"Não há assentos disponíveis para esta classe. Voo ID: "
                        f"{bilhete['voo_id']}, Primeira Classe: {bilhete['prim_classe']}.")
                db_query.execute("""UPDATE bilhete SET lugar = %s, no_serie = %s
                    WHERE id = %s""",
                    (assento["lugar"], voo["no_serie"], bilhete_id))
    except ApiError:
        db_connection.rollback()
        raise
    except Exception as e:
        db_connection.rollback()
        raise ApiError("Erro ao fazer check-in.", {"detalhes": str(e)}) from e
    finally:
        put_db_connection(db_connection)

# API Endpoints
@app.route("/", methods=["GET"])
def list_all_airports():
    """GET all airport names and cities in JSON format."""
    data = get_data_all_airports()
    return jsonify(data), 200

@app.route("/voos/<partida>/", methods=["GET"])
def list_next_departure_flights(partida):
    """GET all flights departing a given airport in the next 12 hours."""
    departure_airport = partida
    if not re.fullmatch(r"[A-Z]{3}", departure_airport):
        raise BadRequestError("Código de aeroporto de partida inválido.")
    data = get_data_next_departure_flights(departure_airport)
    return jsonify(data), 200

@app.route("/voos/<partida>/<chegada>/", methods=["GET"])
def list_available_flights_between_airports(partida, chegada):
    """GET the next 3 available flights between the given
        arrival and departure airports."""
    if not re.fullmatch(r"[A-Z]{3}", partida):
        raise BadRequestError("Código de aeroporto de partida inválido.")
    if not re.fullmatch(r"[A-Z]{3}", chegada):
        raise BadRequestError("Código de aeroporto de chegada inválido.")
    data = get_available_flights(partida, chegada)
    return jsonify(data), 200

@app.route("/compra/<int:voo_id>/", methods=["POST"])
def buy_tickets(voo_id):
    """POST request to buy tickets on a flight."""
    data = request.get_json()
    nif = data.get("nif")
    tickets = data.get("bilhetes")
    if not nif or not isinstance(tickets, list) or not tickets:
        raise BadRequestError("Dados inválidos para compra de bilhetes.")
    register_sale(voo_id, nif, tickets)
    return jsonify({"Message": "Compra efetuada com sucesso."}), 201

@app.route("/checkin/<int:bilhete_id>/", methods=["POST"])
def check_in(bilhete_id):
    """PUT request to check-in a passenger's ticket."""
    register_check_in(bilhete_id)
    return jsonify({"Message": "Check-in efetuado com sucesso."}), 200

@app.errorhandler(ApiError)
def handle_api_error(e):
    """Handle custom API errors."""
    return jsonify({
        "error": e.error,
        "message": e.description,
        "status": e.code
    }), e.code

@app.before_request
def check_rate_limit():
    """Enforce rate limit on api endpoints."""
    ip = request.remote_addr
    if is_rate_limited(ip):
        abort(429, description="Too Many Requests")

if __name__ == "__main__":
    app.run()
