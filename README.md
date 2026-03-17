# Aviation DB

A PostgreSQL airline booking database with a Flask REST API, built for the Databases course (Bases de Dados) at Instituto Superior Técnico, 2024/25. It covers flights, aircraft, seats, sales and tickets, and includes integrity constraints, a synthetic data generator, OLAP queries and index tuning.

The schema, identifiers and API messages are in Portuguese, as the course required.

## What's inside

| Path | What it is |
|---|---|
| `container-init/aviacao.sql` | Schema: `aeroporto`, `aviao`, `assento`, `voo`, `venda`, `bilhete` |
| `notebooks/E2-report.ipynb` | Report (in Portuguese): integrity-constraint triggers, views, SQL/OLAP analysis (`ROLLUP`/`CUBE`), and index design with `EXPLAIN ANALYZE` benchmarks |
| `app/app.py` | Flask REST API, using a psycopg connection pool and row locking (`FOR UPDATE NOWAIT` / `SKIP LOCKED`) for concurrent check-ins |
| `data/generate_data.c` | Generator for about 650 MB of realistic synthetic data (`populate.sql`) |
| `data/test_db.py` | Tests for the integrity constraints |

### Integrity constraints

- **RI-1:** at check-in, the ticket's class must match the seat's class, and the seat must belong to the flight's aircraft.
- **RI-2:** tickets sold per class on a flight cannot exceed the number of seats in that class.
- **RI-3:** a sale must happen before the departure of every flight it contains.

They are implemented as triggers in the notebook (section 1). Run those cells to enable them.

## Quick start

Requires Docker.

```sh
git clone https://github.com/inesiscosta/aviation-db.git
cd aviation-db
./run.sh
```

This starts Postgres, the API and a Jupyter server, and drops you into `psql`. On the first start, Postgres creates the `aviacao` database and loads the schema. `./setup.sh` re-imports the schema, which **wipes the data**, so you can reset at any time.

| Service | URL |
|---|---|
| REST API | http://localhost:8080 |
| Jupyter Lab | http://localhost:9999/lab (password `password`) |
| Postgres | `localhost:5432`, app user `flaskapp` / `flask_app`, database `aviacao` |

All credentials are for local development only.

### Loading data

```sh
cd data
cc -O2 -o generate_data generate_data.c -lm
./generate_data                      # writes populate.sql (~650 MB)
docker exec -i bd-ist-postgres-1 psql -U flaskapp -d aviacao < populate.sql
```

The generated data spans January to July 2025:
- at least 10 real European airports, with 2 cities that have 2 airports each
- at least 10 aircraft across 3 or more models, about 10% of rows first class
- at least 5 flights a day, as round trips
- more than 30,000 tickets across more than 10,000 sales
- check-ins on every past flight

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | List all airports |
| `GET` | `/voos/<partida>/` | Flights leaving airport `<partida>` in the next 12 hours |
| `GET` | `/voos/<partida>/<chegada>/` | Next 3 flights from `<partida>` to `<chegada>` that still have tickets |
| `POST` | `/compra/<voo_id>/` | Buy tickets: `{"nif": "123456789", "bilhetes": [{"nome": "Ana", "prim_classe": false}]}` |
| `POST` | `/checkin/<bilhete_id>/` | Check in a ticket, assigning a free seat of the right class |

```sh
curl localhost:8080/voos/LIS/OPO/
curl -X POST localhost:8080/compra/1/ -H 'Content-Type: application/json' \
  -d '{"nif":"123456789","bilhetes":[{"nome":"Ana","prim_classe":false}]}'
```

A purchase runs in a single transaction. If any ticket can't be sold, the whole sale is rolled back and the API returns `409`. Requests are rate-limited per IP.

## Authors

Inês Costa, Lara Marques and Miguel Raposo.

The course teaching staff provided the starter environment (Docker setup, `app/` scaffolding, the `ghcr.io/bdist/notebook` image) and the assignment.

## License

[MIT](LICENSE), except the course starter code in `app/`, which is under the Modified BSD License (see [`app/LICENSE.md`](app/LICENSE.md)).
