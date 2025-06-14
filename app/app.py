#!/usr/bin/python3
"""
Flask API for listing airports and flights,
ticket purchase, and check-in operations.
"""
from logging.config import dictConfig
import re
from flask import Flask, jsonify, request
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

# Setup DB connection
db_pool = psycopg_pool.ConnectionPool(
    conninfo=(
        "dbname=aviacao "
        "user=postgres "
        "password=postgres "
        "host=postgres"
    ),
    min_size=1,
    max_size=10
)

# Custom Exception Classes
class ApiError(Exception):
    """Flask API DB request exceptions."""
    def __init__(self, message, extra=None):
        super().__init__(message)
        self.message = message
        self.extra = extra or {}

# Speciallization of API Exception
class NotFoundError(ApiError):
    """Not found errors."""

class ConflictError(ApiError):
    """Conflict errors."""

class BadRequestError(ApiError):
    """Bad request errors."""

# Database Connection pool helpers
def get_db_connection():
    """Get a db connection from the pool."""
    return db_pool.getconn()

def put_db_connection(connnection):
    """Release db connection into the pool."""
    return db_pool.putconn(connnection)

# Aux functions for API Endpoints
def list_all_airports_db():
    """List all the airports available on the database."""
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(row_factory=dict_row) as db_query:
            db_query.execute("SELECT nome, cidade FROM aeroporto")
            return db_query.fetchall()
    except psycopg.Error as error:
        return ApiError("Erro ao listar todos os aeroportos.", {"details": str(error)})
    finally:
        put_db_connection(db_connection)

def get_departure_filghts_db(departure_airport):
    """Lists all flights departing the selected airport in the next 12 hours."""
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(row_factory=dict_row) as db_query:
            db_query.execute("SELECT 1 FROM aeroporto WHERE codigo = %s", (departure_airport,))
            if not db_query.fetchone():
                raise NotFoundError("Aeroporto de partida não encontrado.", {"partida": departure_airport})
            db_query.execute("SELECT no_serie, hora_partida, chegada FROM voo WHERE partida = %s AND hora_partida BETWEEN NOW() AND NOW() + INTERVAL '12 hours' ORDER BY hora_partida", (departure_airport,))
            data = db_query.fetchall()
            if not data:
                raise NotFoundError("Nenhum voo encontrad para este aeroporto nas próximas 12 horas.", {"partida": departure_airport})
            return data
    except psycopg.Error as error:
        raise ApiError("Erro ao obter os voos a partir.", {"details": str(error)}) from error
    finally:
        put_db_connection(db_connection)

def get_available_flights_db(departure_airport, arrival_airport):
    """Lists the next 3 flights with available capacity."""
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(row_factory=dict_row) as db_query:
            db_query.execute("SELECT 1 FROM aeroporto WHERE codigo = %s", (departure_airport,))
            if not db_query.fetchone():
                raise NotFoundError("Aeroporto de partida não encontrado.", {"partida": departure_airport})
            db_query.execute("SELECT 1 FROM aeroporto WHERE codigo = %s", (arrival_airport,))
            if not db_query.fetchone():
                raise NotFoundError("Aeroporto de chegada não encontrado.", {"chegada": arrival_airport})
            db_query.execute("""
                SELECT v.no_serie, v.hora_partida
                FROM voo v
                LEFT JOIN (
                    SELECT voo_id, COUNT(*) AS vendidos
                    FROM bilhete
                    GROUP BY voo_id
                ) b ON v.id = b.voo_id
                JOIN (
                    SELECT no_serie, COUNT(*) AS capacidade
                    FROM assento
                    GROUP BY no_serie
                ) a ON v.no_serie = a.no_serie
                WHERE v.partida = %s AND v.chegada = %s
                  AND v.hora_partida > NOW()
                  AND (COALESCE(b.vendidos,0) < a.capacidade)
                ORDER BY v.hora_partida
                LIMIT 3
            """, (departure_airport, arrival_airport))
            data = db_query.fetchall()
            if not data:
                raise NotFoundError("Nenhum voo com lugares disponivéis encontrado para a rota desejada.", {"partida": departure_airport, "chegada": arrival_airport})
            return data
    except psycopg.Error as error:
        raise ApiError("Erro ao obter os voos disponíveis.", {"details": str(error)}) from error
    finally:
        put_db_connection(db_connection)

def _get_available_seats(db_query, flight_id, prim_classe):
    """Returns the number of available seats for a given flight and class."""
    db_query.execute("""
        SELECT COUNT(*) AS total
        FROM assento
        WHERE no_serie = (SELECT no_serie FROM voo WHERE id = %s)
          AND prim_classe = %s
          AND lugar NOT IN (
              SELECT lugar FROM bilhete WHERE voo_id = %s AND prim_classe = %s AND lugar IS NOT NULL
          )
    """, (flight_id, prim_classe, flight_id, prim_classe))
    return db_query.fetchone()["total"]

def _get_ticket_price(db_query, flight_id, prim_classe):
    """Get the ticket price for a given flight and class."""
    db_query.execute("SELECT preco FROM bilhete WHERE voo_id = %s AND prim_classe = %s LIMIT 1", (flight_id, prim_classe))
    data = db_query.fetchone()
    return data["preco"] if data else None

def buy_tickets_db(flight_id, nif, tickets_data):
    """Buys tickets for the flight, ensuring availability for the requested class."""
    db_connection = get_db_connection()
    try:
        with db_connection.transaction():
            with db_connection.cursor(row_factory=dict_row) as db_query:
                db_query.execute("INSERT INTO venda (nif_cliente, balcao, hora) VALUES (%s, NULL, NOW()) RETURNING codigo_reserva", (nif,))
                reservation_code = db_query.fetchone()["codigo_reserva"]
                for ticket in tickets_data:
                    available = _get_available_seats(db_query, flight_id, ticket["prim_classe"])
                    if available == 0:
                        raise ConflictError(f"Não há mais bilhetes disponíveis de {'Primeira classe' if ticket['prim_classe'] else 'classe Económica'}.")
                    price_row = _get_ticket_price(db_query, flight_id, ticket["prim_classe"])
                    if price_row is None:
                        raise NotFoundError("Preço não encontrado para o voo e classe especificados.", {"First class": ticket["prim_classe"]})
                    db_query.execute(
                        "INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe, lugar, no_serie) VALUES (%s, %s, %s, %s, %s, NULL, NULL) RETURNING id",
                        (flight_id, reservation_code, ticket["nome"], price_row, ticket["prim_classe"])
                    )
        return reservation_code
    except ApiError:
        db_connection.rollback()
        raise
    except Exception as error:
        db_connection.rollback()
        raise ApiError("Erro ao comprar bilhetes.", {"details": str(error)}) from error
    finally:
        put_db_connection(db_connection)

def checkin_db(bilhete_id):
    """Checks in the passenger, assigns a seat to the ticket in the corresponding class."""
    db_connection = get_db_connection()
    try:
        with db_connection.transaction():
            with db_connection.cursor(row_factory=dict_row) as db_query:
                db_query.execute("SELECT voo_id, prim_classe FROM bilhete WHERE id = %s", (bilhete_id,))
                bilhete = db_query.fetchone()
                if not bilhete:
                    raise NotFoundError("Bilhete não encontrado.", {"bilhete_id": bilhete_id})
                db_query.execute("SELECT no_serie FROM voo WHERE id = %s", (bilhete["voo_id"],))
                voo = db_query.fetchone()
                if not voo:
                    raise NotFoundError("Voo não encontrado.", {"voo_id": bilhete["voo_id"]})
                db_query.execute("SELECT lugar FROM assento WHERE no_serie = %s AND prim_classe = %s AND (lugar, no_serie) NOT IN (SELECT lugar, no_serie FROM bilhete WHERE voo_id = %s AND lugar IS NOT NULL AND no_serie IS NOT NULL) LIMIT 1", (voo["no_serie"], bilhete["prim_classe"], bilhete["voo_id"]))
                assento = db_query.fetchone()
                if not assento:
                    raise ConflictError("Não há assentos disponíveis para esta classe.", {"classe": bilhete["prim_classe"], "voo_id": bilhete["voo_id"]})
                db_query.execute("UPDATE bilhete SET lugar = %s, no_serie = %s WHERE id = %s", (assento["lugar"], voo["no_serie"], bilhete_id))
        return assento["lugar"]
    except ApiError:
        db_connection.rollback()
        raise
    except Exception as error:
        db_connection.rollback()
        raise ApiError("Erro ao fazer check-in.", {"details": str(error)}) from error
    finally:
        put_db_connection(db_connection)


# API Endpoints
@app.route("/", methods=["GET"])
def list_all_airports():
    """GET all airport names and cities in JSON format."""
    try:
        data = list_all_airports_db()
        return jsonify(data), 200
    except ApiError as error:
        return jsonify({"Error": error.message, **error.extra}), 500

@app.route("/voos/<partida>", methods=["GET"])
def get_departure_filghts(partida):
    """GET all flights departing a given airport in the next 12 hours."""
    departure_airport = partida
    if not re.fullmatch(r"[A-Z]{3}", departure_airport):
        return jsonify({"Error": "Código de aeroporto inválido."}), 400
    try:
        data = get_departure_filghts_db(departure_airport)
        return jsonify(data), 200
    except NotFoundError as error:
        return jsonify({"Error": error.message, **error.extra}), 404
    except ApiError as error:
        return jsonify({"Error": error.message, **error.extra}), 500

@app.route("/voos/<partida>/<chegada>", methods=["GET"])
def get_available_filghts(partida, chegada):
    """GET the next 3 available flights between the given
        arrival and departure airports."""
    if not re.fullmatch(r"[A-Z]{3}", partida):
        return jsonify({"Error": "Código de aeroporto de partida inválido."}), 400
    if not re.fullmatch(r"[A-Z]{3}", chegada):
        return jsonify({"Error": "Código de aeroporto de chegada inválido."}), 400
    try:
        data = get_available_flights_db(partida, chegada)
        return jsonify(data), 200
    except NotFoundError as error:
        return jsonify({"Error": error.message, **error.extra}), 404
    except ApiError as error:
        return jsonify({"Error": error.message, **error.extra}), 500

@app.route("/compra/<int:voo_id>/", methods=["POST"])
def buy_tickets(voo_id):
    """POST request to buy tickets on a flight."""
    data = request.get_json()
    nif = data.get("nif")
    tickets = data.get("bilhetes")
    if not nif or not isinstance(tickets, list) or not tickets:
        return jsonify({"Error": "Dados de compra inválidos."}), 400
    try:
        reservation_code = buy_tickets_db(voo_id, nif, tickets)
        return jsonify({"Message": "Compra efetuada com sucesso.",
            "codigo_reserva": reservation_code}), 201
    except NotFoundError as error:
        return jsonify({"Error": error.message, **error.extra}), 404
    except ConflictError as error:
        return jsonify({"Error": error.message, **error.extra}), 409
    except BadRequestError as error:
        return jsonify({"Error": error.message, **error.extra}), 400
    except ApiError as error:
        return jsonify({"Error": error.message, **error.extra}), 500

@app.route("/checkin/<int:bilhete_id>/", methods=["PUT"])
def checkin_bilhete(bilhete_id):
    """PUT request to check-in a passenger's ticket."""
    try:
        seat = checkin_db(bilhete_id)
        return jsonify({"Message": "Check-in efetuado com sucesso.",
            "lugar": seat}), 200
    except NotFoundError as error:
        return jsonify({"Error": error.message, **error.extra}), 404
    except ConflictError as error:
        return jsonify({"Error": error.message, **error.extra}), 409
    except ApiError as error:
        return jsonify({"Error": error.message, **error.extra}), 500

if __name__ == "__main__":
    app.run()
