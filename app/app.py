#!/usr/bin/python3
import os
import psycopg
import psycopg_pool
from psycopg.rows import dict_row
from flask import Flask, jsonify, request
from logging.config import dictConfig


dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)s - %(funcName)20s(): %(message)s",
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

def get_db_connection():
    """Get a db connection from the pool."""
    return db_pool.getconn()

def put_db_connection(connnection):
    """Realese db connection into the pool."""
    return db_pool.putconn(connnection)

def list_all_airports_db():
    """List all the airports available on the database."""
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(row_factory=dict_row) as db_query:
            db_query.execute("SELECT nome, cidade FROM aeroporto ORDER BY cidade, nome;")
            return db_query.fetchall(), None
    except Exception as error:
        return None, str(error)
    finally:
        put_db_connection(db_connection)

def get_departure_filghts_db(departure_airport):
    """Lists all flights departing the selected airport in the next 12 hours."""
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(row_factory=dict_row) as db_query:
            db_query.execute("SELECT no_serie, hora_partida, chegada FROM voo WHERE partida = %s AND hora_partida BETWEEN NOW() AND NOW() + INTERVAL '12 hours' ORDER BY hora_partida", (departure_airport,))
            return db_query.fetchall(), None
    except Exception as error:
        return None, str(error)
    finally:
        put_db_connection(db_connection)

def get_available_flights_db(departure_airport, arrival_airport):
    """Lists the next 3 flights with available capacity."""
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(row_factory=dict_row) as db_query:
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
            return db_query.fetchall(), None
    except Exception as e:
        return None, str(e)
    finally:
        put_db_connection(db_connection)

def buy_tickets_db(flight_id, nif, tickets_data):
    """Buys tickets for the flight."""
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(row_factory=dict_row) as db_query:
            db_query.execute("INSERT INTO venda (nif_cliente, balcao, hora) VALUES (%s, NULL, NOW()) RETURNING codigo_reserva", (nif,))
            reservation_code = db_query.fetchone()["codigo_reserva"]
            for ticket in tickets_data:
                db_query.execute(
                    """
                    SELECT preco
                    FROM bilhete
                    WHERE voo_id = %s AND prim_classe = %s
                    """,
                    (flight_id, ticket["prim_classe"])
                )
                result = db_query.fetchone()
                if result is None:
                    raise ValueError("Preço não encontrado para o voo e classe especificados.")
                price = result["preco"]
            print(price)
            for ticket in tickets_data:
                print("YOOO")
                db_query.execute("INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe, lugar, no_serie) VALUES (%s, %s, %s, %s, %s, NULL, NULL) RETURNING id", (flight_id, reservation_code, ticket["nome"], price, ticket["prim_classe"]))
                db_connection.commit()
            return reservation_code, None
    except Exception as error:
        db_connection.rollback()
        return None, str(error)
    finally:
        put_db_connection(db_connection)

@app.route("/", methods=["GET"])
def list_all_airports():
    """GET request returns a list of all airports names and cities in json format."""
    data, error = list_all_airports_db()
    if error:
        return jsonify({"Error": error}), 500
    return jsonify(data)

@app.route("/voos/<partida>", methods=["GET"])
def get_departure_filghts(partida):
    """GET request returns a list of all filghts departing an airport in the next 12 hours."""
    departure_airport = partida.upper()[:3]
    data, error = get_departure_filghts_db(departure_airport)
    if error:
        return jsonify({"Error": error}), 500
    return jsonify(data)

@app.route("/voos/<partida>/<chegada>", methods=["GET"])
def get_available_filghts(partida, chegada):
    """GET request returns a list of the next 3 flights with available capacity."""
    departure_airport = partida.upper()[:3]
    arrival_airport = chegada.upper()[:3]
    data, error = get_available_flights_db(departure_airport, arrival_airport)
    if error:
        return jsonify({"Error": error}), 500
    return jsonify(data)

@app.route("/compra/<int:voo_id>/", methods=["POST"])
def buy_tickets(voo_id):
    """POST request to buy tickets on a flight."""
    data = request.get_json()
    nif = data.get("nif")
    tickets = data.get("bilhetes")
    if not nif or not isinstance(tickets, list) or not tickets:
        return jsonify({"Error": "Dados de compra inválidos."}), 400
    reserve_code, error = buy_tickets_db(voo_id, nif, tickets)
    if error:
        return jsonify({"Error": error}), 500
    return jsonify({"message": "Compra efetuada com sucesso.", "codigo_reserva": reserve_code}), 201

if __name__ == "__main__":
    app.run()
