import random
from datetime import datetime, timedelta

# Airports:
airports = [
    ('LIS', 'Humberto Delgado', 'Lisboa', 'Portugal'),
    ('PRT', 'Portela', 'Lisboa', 'Portugal'),
    ('OPO', 'Francisco Sá Carneiro', 'Porto', 'Portugal'),
    ('CDG', 'Charles de Gaulle', 'Paris', 'France'),
    ('ORY', 'Orly', 'Paris', 'France'),
    ('FRA', 'Frankfurt', 'Frankfurt', 'Germany'),
    ('AMS', 'Schiphol', 'Amsterdam', 'Netherlands'),
    ('MAD', 'Barajas', 'Madrid', 'Spain'),
    ('BCN', 'El Prat', 'Barcelona', 'Spain'),
    ('VIE', 'Vienna Intl', 'Vienna', 'Austria'),
    ('BRU', 'Brussels', 'Brussels', 'Belgium'),
    ('ZRH', 'Zurich', 'Zurich', 'Switzerland'),
]

# Airplanes: (150-200 seats, 10% first class)
models = [
    ('A320', 180),
    ('B737', 160),
    ('A321', 200),
]
airplanes = []
for i in range(10):
    model = models[i % len(models)]
    no_serie = f'CS-{1000+i}'
    airplanes.append((no_serie, model[0], model[1]))

# Seats per airplane
def generate_seats(no_serie, total_seats):
    """Generates the seats for each plane, 10% is first class."""
    seats = []
    rows = total_seats // 6
    first_class_rows = max(1, int(rows * 0.1))
    for row in range(1, rows+1):
        for seat in 'ABCDEF':
            lugar = f"{row}{seat}"
            prim_classe = row <= first_class_rows
            seats.append((lugar, no_serie, prim_classe))
    return seats

# Generate flights: 5 per day, 1 Jan - 31 Jul 2025, round trips, all airports, all airplanes
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 7, 31)
days = (end_date - start_date).days + 1
flights_per_day = 5

flight_id = 1
flights = []
flight_plan = []
route_pairs = set()
for day in range(days):
    date = start_date + timedelta(days=day)
    used_airplanes = airplanes.copy()
    random.shuffle(used_airplanes)
    used_pairs = set()
    for sql_file in range(flights_per_day):
        # Pick two different airports
        while True:
            a1, a2 = random.sample(airports, 2)
            pair = tuple(sorted((a1[0], a2[0])))
            if pair not in used_pairs:
                used_pairs.add(pair)
                break
        # Assign airplane
        no_serie, model, cap = used_airplanes[sql_file % len(used_airplanes)]
        # Departure time
        dep_time = datetime(date.year, date.month, date.day, 6 + sql_file*3, 0)
        arr_time = dep_time + timedelta(hours=2)
        # Outbound
        flights.append((flight_id, no_serie, dep_time, arr_time, a1[0], a2[0]))
        flight_plan.append((flight_id, a1[0], a2[0], no_serie))
        route_pairs.add((a1[2], a2[2]))  # (cidade_partida, cidade_chegada)
        flight_id += 1
        # Return
        flights.append((flight_id, no_serie, arr_time + timedelta(hours=1), arr_time + timedelta(hours=3), a2[0], a1[0]))
        flight_plan.append((flight_id, a2[0], a1[0], no_serie))
        route_pairs.add((a2[2], a1[2]))
        flight_id += 1

def price_for_route(cidade_partida, cidade_chegada):
    """Generates prices for each route."""
    base_1c = 250
    base_2c = 120

    if 'Paris' in (cidade_partida, cidade_chegada) or 'Lisboa' in (cidade_partida, cidade_chegada):
        base_1c += 50
        base_2c += 20
    return (base_1c + random.randint(0, 50), base_2c + random.randint(0, 30))

# Build price table for all used city pairs
preco_rota_dict = {}
for cidade_partida, cidade_chegada in route_pairs:
    if (cidade_partida, cidade_chegada) not in preco_rota_dict:
        preco_1c, preco_2c = price_for_route(cidade_partida, cidade_chegada)
        preco_rota_dict[(cidade_partida, cidade_chegada)] = (preco_1c, preco_2c)

# Generate sales and tickets: 30,000 tickets, 10,000 sales, all flights have 1st and 2nd class tickets
tickets = []
sales = []
ticket_id = 1
sale_id = 1
random.seed(42)
for i in range(10000):
    nif = f"{random.randint(100000000,999999999)}"
    balcao = random.choice(airports)[0]
    # Sale time: random before flight
    flight = random.choice(flights)
    sale_time = flight[2] - timedelta(days=random.randint(2, 30), hours=random.randint(0, 23))
    sales.append((sale_id, nif, balcao, sale_time))
    # Each sale: 3 tickets (mix of classes, and a family sale)
    for j in range(3):
        voo_id = flight[0]
        prim_classe = (j == 0)
        nome = f"Passageiro_{sale_id}_{j+1}"
        # Use consistent pricing from the preco_rota table
        partida_code = flight[4]
        chegada_code = flight[5]
        partida_cidade = next(a[2] for a in airports if a[0] == partida_code)
        chegada_cidade = next(a[2] for a in airports if a[0] == chegada_code)
        preco_1c, preco_2c = preco_rota_dict.get((partida_cidade, chegada_cidade), (200.0, 100.0))
        preco = preco_1c if prim_classe else preco_2c
        lugar = None
        no_serie = None
        # Simulates the check-in (for simplicity reasons it is done after the flight left)
        if flight[2] < datetime.now():
            # Find a seat
            airplane = next(a for a in airplanes if a[0] == flight[1])
            seats = generate_seats(airplane[0], airplane[2])
            seat_candidates = [s for s in seats if s[2] == prim_classe]
            lugar, no_serie, _ = random.choice(seat_candidates)
        tickets.append((ticket_id, voo_id, sale_id, nome, preco, prim_classe, lugar, no_serie))
        ticket_id += 1
    sale_id += 1

# Write SQL
with open("populate.sql", "w", encoding="utf-8") as sql_file:
    # Airports
    for code, name, city, country in airports:
        sql_file.write("INSERT INTO aeroporto (codigo, nome, cidade, pais) VALUES ")
        sql_file.write(f"('{code}', '{name}', '{city}', '{country}');\n")

    # Airplanes
    for no_serie, model, cap in airplanes:
        sql_file.write("INSERT INTO aviao (no_serie, modelo) VALUES ")
        sql_file.write(f"('{no_serie}', '{model}');\n")

    # Seats
    for no_serie, model, cap in airplanes:
        for lugar, serie, prim_classe in generate_seats(no_serie, cap):
            sql_file.write("INSERT INTO assento (lugar, no_serie, prim_classe) VALUES ")
            sql_file.write(f"('{lugar}', '{serie}', {'true' if prim_classe else 'false'});\n")

    # Create preco_rota table
    sql_file.write("""
      CREATE TABLE IF NOT EXISTS preco_rota (
          cidade_partida VARCHAR(255) NOT NULL,
          cidade_chegada VARCHAR(255) NOT NULL,
          preco_1c NUMERIC(7,2) NOT NULL,
          preco_2c NUMERIC(7,2) NOT NULL,
          PRIMARY KEY (cidade_partida, cidade_chegada)
      );\n""")

    # Fill preco_rota
    for (cidade_partida, cidade_chegada), (preco_1c, preco_2c) in preco_rota_dict.items():
        sql_file.write("INSERT INTO preco_rota (cidade_partida, cidade_chegada, preco_1c, preco_2c) VALUES ")
        sql_file.write(f"('{cidade_partida}', '{cidade_chegada}', {preco_1c:.2f}, {preco_2c:.2f});\n")

    # Flights
    for fid, no_serie, dep, arr, partida, chegada in flights:
        sql_file.write("INSERT INTO voo (id, no_serie, hora_partida, hora_chegada, partida, chegada) VALUES ")
        sql_file.write(f"({fid}, '{no_serie}', '{dep.strftime('%Y-%m-%d %H:%M:%S')}', '{arr.strftime('%Y-%m-%d %H:%M:%S')}', '{partida}', '{chegada}');\n")

    # Sales
    for sid, nif, balcao, hora in sales:
        sql_file.write("INSERT INTO venda (codigo_reserva, nif_cliente, balcao, hora) VALUES ")
        sql_file.write(f"({sid}, '{nif}', '{balcao}', '{hora.strftime('%Y-%m-%d %H:%M:%S')}');\n")

    # Tickets
    for tid, voo_id, sale_id, nome, preco, prim_classe, lugar, no_serie in tickets:
        if lugar:
            lugar_sql = f"'{lugar}'"
        else:
            lugar_sql = "NULL"
        if no_serie:
            no_serie_sql = f"'{no_serie}'"
        else:
            no_serie_sql = "NULL"
        sql_file.write("INSERT INTO bilhete (id, voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe, lugar, no_serie) VALUES ")
        sql_file.write(f"({tid}, {voo_id}, {sale_id}, '{nome}', {preco:.2f}, {'true' if prim_classe else 'false'}, {lugar_sql}, {no_serie_sql});\n")
