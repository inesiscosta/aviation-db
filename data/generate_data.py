from dataclasses import dataclass, field
from datetime import datetime, timedelta
import names
import random

@dataclass
class Airport:
    iata_code: str
    name: str
    city: str
    country: str

@dataclass
class Airplane:
    serial_no: str
    model: str
    total_seats: int
    seats: list['Seat'] = field(default_factory=list)

@dataclass
class Model:
    name: str
    total_seats: int

@dataclass
class Seat:
    id: str
    first_class: bool
    airplane: 'Airplane'

@dataclass
class Flight:
    airplane: Airplane
    departure_airport: Airport
    departure_datetime: datetime
    arrival_airport: Airport
    arrival_datetime: datetime

@dataclass
class Sale:
    retail_counter: Airport
    nif: str
    datetime: datetime

@dataclass
class Ticket:
    flight: Flight
    sale: Sale
    name: str
    price: float
    seat: Seat
    first_class: bool

# Airports
airports_data = [
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
# Create Airport objects using the provided data
airports = [Airport(*data) for data in airports_data]

# Airplane models
models = [
    Model('A220-300', 145),
    Model('B737-800', 160),
    Model('A320', 186),
    Model('B737 MAX 8', 189),
    Model('A321', 244),
    Model('B787-8', 242),
]

# Country prefixes for serial numbers
country_prefixes = ['CS', 'D', 'G', 'F', 'I', 'OE', 'EC', 'PH', 'HB']

# Generate serial numbers for airplanes
# Format: <country_prefix>-<manufacturer_letter><number>
def generate_serial_number(model_name):
    # Randomly select a country prefix for this serial number
    country_prefix = random.choice(country_prefixes)
    # The first letter of the model name is used as the manufacturer letter (as per real-world practice)
    manufacturer_letter = model_name[0]
    # Generate a random 4-digit number
    number = random.randint(1000, 9999)
    # Combine to form the serial number
    return f'{country_prefix}-{manufacturer_letter}{number}'

# Generate a list of 20 airplanes with unique serial numbers
airplanes = []
# Track serial numbers to ensure uniqueness
used_serials = set()
# Track used models to ensure all models are used at least once
used_models = set()
# Generate 20 airplanes
for i in range(20):
    # Randomly select a model for this airplane and mark it as used
    model = random.choice(models)
    used_models.add(model.name)
    # Generate a serial number for this airplane
    serial_no = generate_serial_number(model.name)
    # If the serial number is already used, generate a new one until it's unique
    while serial_no in used_serials:
        serial_no = generate_serial_number(model.name)
    # Mark this serial number as used
    used_serials.add(serial_no)
    # Create and save this Airplane
    airplanes.append(Airplane(serial_no, model.name, model.total_seats))

# Validate that all models are used at least once
print(f"All models used: {all(model.name in used_models for model in models)}")

# Generate seats for each airplane based on airplane capacity
seat_letters = 'ABCDEF' # Assuming a maximum of 6 seats per row (normally 3 on each side of the aisle)
seats_per_row = len(seat_letters) # 6
for airplane in airplanes:
    seats = []
    # Ceiling the total number of rows based on the total seats and seats per row.
    total_rows = (airplane.total_seats + seats_per_row - 1) // seats_per_row
    # Calculate the number of first class rows (10% of total rows, rounded down)
    first_class_rows = int(total_rows * 0.1)
    for i in range(airplane.total_seats):
        # Calculate the row number
        row_number = i // seats_per_row + 1
        # Calculate indice of the seat letter
        col_letter = seat_letters[i % seats_per_row]
        id = f"{row_number}{col_letter}"
        # Determine if this seat is first class (first 10% of rows)
        is_first_class_seat = row_number <= first_class_rows
        # Create and save the Seat
        seats.append(Seat(id, is_first_class_seat, airplane))
    # Save to each plane a list of its seats
    airplane.seats = seats


# Creates a list of all possible pairs of different cities (no city paired with itself), each pair is a tuple: (departure_city, arrival_city)
city_pairs = [
    (airport1.city, airport2.city)
    for airport1 in airports
    for airport2 in airports
    if airport1.city != airport2.city
]
flight_info_dict = {}
# Generate flight information for each city pair
for departure_city, arrival_city in city_pairs:
    # Randomly generate flight time between 60 and 210 minutes (1 to 3.5 hours)
    base_minutes = random.randint(60, 210)
    # Randomly generate base prices for second class between 80.99 and 350.99 euros (prices always end with .99)
    base_price_2c = random.randint(80, 350) + 0.99
    # First class price is 40% more than second class price
    base_price_1c = round(base_price_2c * 1.4, 2)
    # Store the flight information in a dictionary with the city pair as the key
    flight_info_dict[(departure_city, arrival_city)] = {
        "flight_time": base_minutes,
        "price_2c": base_price_2c,
        "price_1c": base_price_1c
    }

# Start date for the flights 1st January 2025
start_date = datetime(2025, 1, 1)
# End date for the flights 31st July 2025
end_date = datetime(2025, 7, 31)
days = (end_date - start_date).days + 1
flights = []
# Track visited airports to ensure all airports are visited
visited_airports = set()
# Track used airplanes to ensure all airplanes are used
used_airplanes = set()
for day in range(days):
    # Increments the days from the start date
    date = start_date + timedelta(days=day)
    # Randomly select 3 airplanes for today's flights
    airplanes_today = random.sample(airplanes, 3)
    for airplane in airplanes_today:
        used_airplanes.add(airplane.serial_no)
        for interval in [(5, 8), (17, 20)]:
            # Departure Flight
            departure_airport = random.choice(airports)
            # Choose an airport in a different city (not same IATA code or city)
            arrival_airport = random.choice([
                airport for airport in airports
                if airport != departure_airport and airport.city != departure_airport.city
            ])
            # Generates random departure time within the specified interval
            departure_hour = random.randint(interval[0], interval[1])
            departure_time = datetime(date.year, date.month, date.day, departure_hour, random.randint(0, 59))
            # Gets predefined flight time
            flight_time = flight_info_dict.get((departure_airport.city, arrival_airport.city), {}).get("flight_time")
            # Calculate arrival time
            arrival_time = departure_time + timedelta(minutes=flight_time)
            # Creates and saves flight
            flights.append(Flight(airplane, departure_airport, departure_time, arrival_airport, arrival_time))
            visited_airports.add(departure_airport.iata_code)
            visited_airports.add(arrival_airport.iata_code)
            # Return flight
            # Generates a random return flight departure time with a delay of 30 to 90 minutes from previous arrival time
            departure_time = arrival_time + timedelta(minutes=random.randint(30, 90))
            # Gets the time for the return flight, the cities are swapped since it's a return flight.
            flight_time = flight_info_dict.get((arrival_airport.city, departure_airport.city), {}).get("flight_time")
            # Calculate arrival time
            arrival_time = departure_time + timedelta(minutes=flight_time)
            # Creates and saves return flight
            flights.append(Flight(airplane, departure_airport, departure_time, arrival_airport, arrival_time))
            visited_airports.add(departure_airport.iata_code)
            visited_airports.add(arrival_airport.iata_code)

# Validate that all airports and airplanes have been visited/used.
print(f"All airports visited: {len(visited_airports) >= len(airports)}")
print(f"All airplanes used: {len(used_airplanes) >= len(airplanes)}")

# Sales and Tickets
sales = []
tickets = []
sale_id = 1
for flight_id, flight in enumerate(flights, start=1):
    # Randomly select the occupancy of this flight between 85% and 100% (this will be the percentage of tickets sold)
    ocupancy = random.randint(85, 100) / 100
    # Calculate the number of tickets to sell based on the occupancy and total seats of the airplane
    num_tickets_to_sell = int(flight.airplane.total_seats * ocupancy)
    # Calculate the number of first class and second class seats available
    first_class_available_seats = [seat for seat in flight.airplane.seats if seat.first_class]
    second_class_available_seats = [seat for seat in flight.airplane.seats if not seat.first_class]
    # While there are tickets to sell, create sales and tickets
    while num_tickets_to_sell > 0:
        # Names must be unique for tickets in the same sale, so we will use a set to track used names.
        used_names = set()
        # Generate a random NIF
        nif = f"{random.randint(100000000,999999999)}"
        # Randomly select a retail counter (airport) for the sale, or None which represents an online sale (40% chance of online sale).
        retail_counter = None if random.random() < 0.4 else random.choice(airports)
        # Generate a random sale time, which is between 1 and 90 days before the flight departure time.
        sale_time = flight.departure_datetime - timedelta(days=random.randint(1, 90), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        # Create and save the sale
        sale = Sale(retail_counter, nif, sale_time)
        sales.append(sale)
        # Randomly determine how many tickets to sell in this sale (between 1 and 5).
        num_sold_tickets = random.randint(1, 5)
        # If there are not enough tickets to sell, adjust the number of sold tickets.
        num_sold_tickets = min(num_sold_tickets, num_tickets_to_sell)
        # For each ticket to sell, randomly choose first class or second class, ensuring that the choice is valid based on available seats.
        for _ in range(num_sold_tickets):
            if first_class_available_seats and second_class_available_seats:
                first_class = random.choice([True, False])
            elif second_class_available_seats:
                first_class = False
            else:
                first_class = True
            # Generate a name for the ticket and ensure it is unique within the sale.
            name = names.get_full_name()
            while name in used_names:
                name = names.get_full_name()
            used_names.add(name)
            # Determine the price and seat based on the class chosen.
            if first_class:
                price = flight_info_dict.get((flight.departure_airport.city, flight.arrival_airport.city), {}).get("price_1c")
                # Select a random first class seat and remove it from the available seats.
                chosen_seat = random.choice(first_class_available_seats)
                first_class_available_seats.remove(chosen_seat)
            else:
                price = flight_info_dict.get((flight.departure_airport.city, flight.arrival_airport.city), {}).get("price_2c")
                # Select a random second class seat and remove it from the available seats.
                chosen_seat = random.choice(second_class_available_seats)
                second_class_available_seats.remove(chosen_seat)
            # Create and save the ticket
            tickets.append(Ticket(flight, sale, name, price, chosen_seat, first_class))
        # Increment the sale ID for the next sale and adjust the number of tickets left to sell.
        sale_id += 1
        num_tickets_to_sell -= num_sold_tickets

# Write SQL statements to populate the database into populate.sql file
with open("populate.sql", "w", encoding="utf-8") as sql_file:

    # Airports
    for airport in airports:
        sql_file.write("INSERT INTO aeroporto (codigo, name, cidade, pais) VALUES ")
        sql_file.write(f"('{airport.iata_code}', '{airport.name}', '{airport.city}', '{airport.country}');\n")

    # Airplanes and Seats
    for airplane in airplanes:
        sql_file.write("INSERT INTO aviao (serial_no, modelo) VALUES ")
        sql_file.write(f"('{airplane.serial_no}', '{airplane.model}');\n")
        for seat in airplane.seats:
            sql_file.write("INSERT INTO assento (id, serial_no, prim_classe) VALUES ")
            sql_file.write(f"('{seat.id}', '{airplane.serial_no}', {'true' if seat.first_class else 'false'});\n")

    # Flights
    for flight_id, flight in enumerate(flights, start=1):
        sql_file.write("INSERT INTO voo (serial_no, departure_datetime, arrival_datetime, partida, chegada) VALUES ")
        sql_file.write(f"('{flight.airplane.serial_no}', '{flight.departure_datetime.strftime('%Y-%m-%d %H:%M:%S')}', '{flight.arrival_datetime.strftime('%Y-%m-%d %H:%M:%S')}', '{flight.departure_airport.iata_code}', '{flight.arrival_airport.iata_code}');\n")

    # Sales
    for sale in sales:
        # Get airport IATA code if its a physical sale in which case there is a retail counter, or pass NULL otherwise to represent an online sale.
        retail_counter = f"'{sale.retail_counter.iata_code}'" if sale.retail_counter is not None else "NULL"
        sql_file.write("INSERT INTO venda (nif_cliente, retail_counter, datetime) VALUES ")
        sql_file.write(f"('{sale.nif}', {retail_counter}, '{sale.datetime.strftime('%Y-%m-%d %H:%M:%S')}');\n")

    # Tickets
    for ticket in tickets:
        # Get the flight ID and sale ID based on their index in the lists (1-based index). Mimicking the behavior of an auto-incrementing primary key (SERIAL).
        flight_id = flights.index(ticket.flight) + 1
        sale_id = sales.index(ticket.sale) + 1
        sql_file.write("INSERT INTO bilhete (voo_id, codigo_reserva, name_passegeiro, price, prim_classe, id, serial_no) VALUES ")
        sql_file.write(f"({flight_id}, {sale_id}, '{ticket.name}', {ticket.price:.2f}, {'true' if ticket.first_class else 'false'}, '{ticket.seat.id}', '{ticket.flight.airplane.serial_no}');\n")
