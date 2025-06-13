import random
import names
from datetime import datetime, timedelta

# Airports in Europe
# Format: (IATA code, name, city, country)
# Cities with multiple airports:
#   - Istanbul (2 airports),
#   - London (3 airports)
#   - Milan (2 airports),
#   - Paris (2 airports),
airports = [
    ('VIE', 'Vienna Intl', 'Vienna', 'Austria'),
    ('PRG', 'Václav Havel', 'Prague', 'Czech Republic'),
    ('CPH', 'Kastrup', 'Copenhagen', 'Denmark'),
    ('CDG', 'Paris Charles de Gaulle', 'Paris', 'France'),
    ('ORY', 'Paris Orly', 'Paris', 'France'),
    ('MUC', 'Munich', 'Munich', 'Germany'),
    ('FCO', 'Fiumicino', 'Rome', 'Italy'),
    ('LIN', 'Linate', 'Milan', 'Italy'),
    ('MXP', 'Malpensa', 'Milan', 'Italy'),
    ('AMS', 'Schiphol', 'Amsterdam', 'Netherlands'),
    ('LIS', 'Humberto Delgado', 'Lisboa', 'Portugal'),
    ('OPO', 'Francisco Sá Carneiro', 'Porto', 'Portugal'),
    ('BCN', 'El Prat', 'Barcelona', 'Spain'),
    ('MAD', 'Barajas', 'Madrid', 'Spain'),
    ('ZRH', 'Zurich', 'Zurich', 'Switzerland'),
    ('IST', 'Istanbul Airport', 'Istanbul', 'Türkiye'),
    ('SAW', 'Sabiha Gökçen', 'Istanbul', 'Türkiye'),
    ('LGW', 'Gatwick', 'London', 'United Kingdom'),
    ('LHR', 'Heathrow', 'London', 'United Kingdom'),
    ('STN', 'Stansted', 'London', 'United Kingdom'),
]

airport_dict = {airport[0]: airport for airport in airports}

# Common Airplane Models for European Routes:
# Format: (Model Name, Total Seats)
models = [
    ('A220-300', 145),
    ('B737-800', 160),
    ('A320', 186),
    ('B737 MAX 8', 189),
    ('A321', 244),
    ('B787-8', 242),
]

# Array of Country Prefixes
country_prefixes = ['CS', 'D', 'G', 'F', 'I', 'OE', 'EC', 'PH', 'HB']

def generate_no_serie(model_name):
    """Generates a unique serial number based on the model name."""
    country_prefix = random.choice(country_prefixes)
    manufacturer_letter = model_name[0]
    number = random.randint(1000, 9999)
    return f'{country_prefix}-{manufacturer_letter}{number}'

def generate_airplanes():
    """Generates a list of airplanes with unique serial numbers."""
    airplanes = []
    used_serials = set()
    for i in range(20):
        model = models[i % len(models)]
        no_serie = generate_no_serie(model[0])
        while no_serie in used_serials:
            no_serie = generate_no_serie(model[0])
        used_serials.add(no_serie)
        airplanes.append((no_serie, model[0], model[1]))
    return airplanes

# Airplanes: 25 airplanes with unique serial numbers
# Format: (no_serie, model, total_seats)
airplanes = generate_airplanes()
airplanes_dict = {airplane[0]: airplane for airplane in airplanes}

# Seats per airplane
# Format: (no_serie, model, total_seats)
def generate_seats(no_serie, total_seats):
    """Generate seats with ~10% first class using index math."""
    seats = []
    seat_letters = 'ABCDEF'
    seats_per_row = len(seat_letters) # 6 seats per row (A-F)

    total_rows = (total_seats + seats_per_row - 1) // seats_per_row  # ceiling division
    first_class_rows = int(total_rows * 0.1)

    for i in range(total_seats):
        row = i // seats_per_row + 1  # row numbers start at 1
        col = i % seats_per_row       # index into seat_letters
        lugar = f"{row}{seat_letters[col]}"
        is_first_class_seat = row <= first_class_rows
        seats.append((lugar, no_serie, is_first_class_seat))
    return seats

# Generate all possible city pairs (excluding same city)
city_pairs = [(a1[2], a2[2]) for a1 in airports for a2 in airports if a1[2] != a2[2]]

# Assign a random flight time (in minutes) and price for each direction
flight_info_dict = {}
for dep_city, arr_city in city_pairs:
    base_minutes = random.randint(60, 210) # 60-210 min (1 to 3.5 hours)
    base_price_2c = random.randint(80, 350) + 0.99 # 80-350 EUR for 2nd class
    base_price_1c = round(base_price_2c * 1.2, 2)
    flight_info_dict[(dep_city, arr_city)] = {
        "flight_time": base_minutes,
        "preco_2c": base_price_2c,
        "preco_1c": base_price_1c
    }

# Flights: ≥5 per day between 1 Jan - 31 Jul 2025
# Format: (no_serie, hora_partida, hora_chegada, partida, chegada)
# Each airplane is used, all airports are visited, every flight is followed by a return flight,
# and each airplane departs from its previous arrival airport.
def generate_flights():
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 7, 31)
    days = (end_date - start_date).days + 1

    # Assign each airplane a random starting airport
    airplane_locations = {} # key: airplane serial_no, value: airport code
    shuffled_airports = airports.copy()
    random.shuffle(shuffled_airports)
    for idx, airplane in enumerate(airplanes):
        airport = shuffled_airports[idx % len(shuffled_airports)]
        random_hour = random.randint(0, 23)
        random_minute = random.randint(0, 59)
        arrival_time = datetime(2025, 1, 1, random_hour, random_minute)
        airplane_locations[airplane[0]] = (airport[0], arrival_time)

    flights = []
    visited_airports = set()

    for day in range(days):
        date = start_date + timedelta(days=day)
        airplanes_today = airplanes.copy()
        random.shuffle(airplanes_today)
        for airplane in airplanes_today:
            no_serie, _, _ = airplane
            for interval in [(5, 8), (17, 20)]:
                dep_airport, arrival_time = airplane_locations[no_serie]
                arr_airport = random.choice([a for a in airports if a[0] != dep_airport])[0]
                # Outbound flight
                hour = random.randint(interval[0], interval[1])
                minute = random.randint(0, 59)
                dep_time = datetime(date.year, date.month, date.day, hour, minute)
                while dep_time <= arrival_time + timedelta(hours=1):
                    hour = random.randint(interval[0], interval[1])
                    minute = random.randint(0, 59)
                    dep_time = datetime(date.year, date.month, date.day, hour, minute)
                departure_city = airport_dict[dep_airport][2]
                arrival_city = airport_dict[arr_airport][2]
                flight_time = flight_info_dict.get((departure_city, arrival_city), {}).get("flight_time")
                arr_time = dep_time + timedelta(minutes=flight_time)
                flights.append((no_serie, dep_time, arr_time, dep_airport, arr_airport))
                visited_airports.add(dep_airport)
                visited_airports.add(arr_airport)
                airplane_locations[no_serie] = (arr_airport, arr_time)
                # Return flight
                return_airport = dep_airport
                return_dep_time = arr_time + timedelta(minutes=random.randint(30, 60))
                flight_time = flight_info_dict.get((arrival_city, departure_city), {}).get("flight_time")
                return_arrival_time = return_dep_time + timedelta(minutes=flight_time)
                flights.append((no_serie, return_dep_time, return_arrival_time, arr_airport, return_airport))
    return flights, len(visited_airports) >= len(airports)

# Generate flights and route_pairs
flights, valid = generate_flights()

# Sales and Tickets: >=10,000 sales and >= 30,000 tickets
sales = []
tickets = []
sale_id = 1
for flight_id, flight in enumerate(flights, start=1):
    airplane = airplanes_dict[flight[0]]
    capacity = airplane[2]  # Total seats in the airplane
    ocupancy = random.randint(85, 100) / 100  # Random occupancy between 85% and 100%
    num_tickets = int(capacity * ocupancy)
    first_class_available_tickets = capacity // 10  # 10% of total seats are first class
    second_class_available_tickets = capacity - first_class_available_tickets
    first_class_available_seats = [seat for seat in generate_seats(airplane[0], capacity) if seat[2] == True]
    second_class_available_seats = [seat for seat in generate_seats(airplane[0], capacity) if seat[2] == False]
    while num_tickets > 0:
        used_names = set()
        nif = f"{random.randint(100000000,999999999)}"
        balcao = random.choice(airports)[0]
        airplane_departure_time = flight[1]
        sale_time = airplane_departure_time - timedelta(days=random.randint(1, 90), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        sale = (nif, balcao, sale_time)
        sales.append(sale)
        num_sold_tickets = random.randint(1, 5)
        if num_sold_tickets > num_tickets:
            num_sold_tickets = num_tickets
        for _ in range(num_sold_tickets):
            airplane_serial_no = flight[0]
            if first_class_available_tickets == 0:
                first_class = False
            elif second_class_available_tickets == 0:
                first_class = True
            else:
                first_class = random.choice([True, False])
            nome = names.get_full_name()
            while nome in used_names:
                nome = names.get_full_name()
            used_names.add(nome)
            partida_code = flight[4]
            chegada_code = flight[5]
            partida_cidade = airport_dict[partida_code][2]
            chegada_cidade = airport_dict[chegada_code][2]
            if first_class:
                preco = flight_info_dict.get((partida_cidade, chegada_cidade), {}).get("preco_1c")
                chosen_seat = random.choice(first_class_available_seats)
                first_class_available_seats.remove(chosen_seat)
                first_class_available_tickets -= 1
            else:
                preco = flight_info_dict.get((partida_cidade, chegada_cidade), {}).get("preco_2c")
                chosen_seat = random.choice(second_class_available_seats)
                second_class_available_seats.remove(chosen_seat)
                second_class_available_tickets -= 1
            lugar, _, _ = chosen_seat
            tickets.append((flight_id, sale_id, nome, preco, first_class, lugar, airplane_serial_no))
        sale_id += 1
        num_tickets -= num_sold_tickets

# Write SQL
with open("populate.sql", "w", encoding="utf-8") as sql_file:
    # Airports
    for code, name, city, country in airports:
        sql_file.write("INSERT INTO aeroporto (codigo, nome, cidade, pais) VALUES ")
        sql_file.write(f"('{code}', '{name}', '{city}', '{country}');\n")

    # Airplanes and Respective Seats
    for no_serie, model, capacity in airplanes:
        sql_file.write("INSERT INTO aviao (no_serie, modelo) VALUES ")
        sql_file.write(f"('{no_serie}', '{model}');\n")
        for lugar, serie, first_class in generate_seats(no_serie, capacity):
            sql_file.write("INSERT INTO assento (lugar, no_serie, prim_classe) VALUES ")
            sql_file.write(f"('{lugar}', '{serie}', {'true' if first_class else 'false'});\n")

    # Flights
    for flight_id, (no_serie, partida, chegada, dep_airport, arr_airport) in enumerate(flights, start=1):
        sql_file.write("INSERT INTO voo (no_serie, hora_partida, hora_chegada, partida, chegada) VALUES ")
        sql_file.write(f"('{no_serie}', '{partida.strftime('%Y-%m-%d %H:%M:%S')}', '{chegada.strftime('%Y-%m-%d %H:%M:%S')}', '{dep_airport}', '{arr_airport}');\n")

    # Sales
    for sale in sales:
        nif, balcao, hora = sale
        sql_file.write("INSERT INTO venda (nif_cliente, balcao, hora) VALUES ")
        sql_file.write(f"('{nif}', '{balcao}', '{hora.strftime('%Y-%m-%d %H:%M:%S')}');\n")

    # Tickets
    for ticket in tickets:
        flight_id, sale_id, nome, preco, first_class, lugar, no_serie = ticket
        sql_file.write("INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe, lugar, no_serie) VALUES ")
        sql_file.write(f"({flight_id}, {sale_id}, '{nome}', {preco:.2f}, {'true' if first_class else 'false'}, '{lugar}', '{no_serie}');\n")
