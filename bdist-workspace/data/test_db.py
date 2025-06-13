from datetime import datetime, timedelta
import psycopg2

def print_test_result(test_name, expected_result, actual_result, counters, details=""):
    """Print test results"""
    if expected_result == actual_result:
        status = "✓ PASS"
        counters['passed'] += 1
    else:
        status = "✗ FAIL"
        counters['failed'] += 1

    print(f"{status} | {test_name}")
    if details:
        print(f"     {details}")
    if expected_result != actual_result:
        print(f"     Expected: {expected_result}, Got: {actual_result}")
    print()

def setup_minimal_data(db_query, db_connection):
    """Setup minimal test data"""
    print("Setting up minimal test data...")

    # Clean all db data
    db_query.execute("TRUNCATE TABLE bilhete, venda, voo, assento, aviao, aeroporto RESTART IDENTITY CASCADE")

    # Insert new Test Data
    airports = [
        ('LIS', 'Aeroporto Humberto Delgado', 'Lisboa', 'Portugal'),
        ('OPO', 'Aeroporto Francisco Sá Carneiro', 'Porto', 'Portugal'),
        ('CDG', 'Charles de Gaulle Airport', 'Paris', 'France'),
    ]
    for airport in airports:
        db_query.execute(
            "INSERT INTO aeroporto (codigo, nome, cidade, pais) VALUES (%s, %s, %s, %s)",
            airport
        )
    db_query.execute("INSERT INTO aviao (no_serie, modelo) VALUES ('CS-TEST', 'Test Aircraft')")
    seats = [
        ('1A', 'CS-TEST', True),   # First class
        ('1B', 'CS-TEST', True),   # First class
        ('2A', 'CS-TEST', False),  # Economy
        ('2B', 'CS-TEST', False),  # Economy
        ('3A', 'CS-TEST', False),  # Economy
        ('3B', 'CS-TEST', False),  # Economy
    ]
    for seat in seats:
        db_query.execute(
            "INSERT INTO assento (lugar, no_serie, prim_classe) VALUES (%s, %s, %s)",
            seat
        )
    # Flight one day in the future (valid data)
    future_time = datetime.now() + timedelta(days=1)
    db_query.execute(
        "INSERT INTO voo (no_serie, hora_partida, hora_chegada, partida, chegada) VALUES (%s, %s, %s, %s, %s)",
        ('CS-TEST', future_time, future_time + timedelta(hours=2), 'LIS', 'OPO')
    )
    db_connection.commit()
    print("✓ Test data setup complete\n")

def test_ri1_checkin_validation(db_query, db_connection, counters):
    """Test RI-1: Check-in validation"""
    print("=" * 60)
    print("TESTING RI-1: CHECK-IN VALIDATION")
    print("=" * 60)

    # Create a valid sale and ticket
    sale_time = datetime.now() - timedelta(hours=1)
    db_query.execute("INSERT INTO venda (nif_cliente, balcao, hora) VALUES ('123456789', 'LIS', %s) RETURNING codigo_reserva", (sale_time,))
    codigo_reserva = db_query.fetchone()[0]

    db_query.execute("INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe) VALUES (1, %s, 'Test Passenger', 100.0, true) RETURNING id", (codigo_reserva,))
    ticket_id = db_query.fetchone()[0]
    db_connection.commit()

    # Test 1: Valid check-in (correct class and airplane)
    try:
        db_query.execute("UPDATE bilhete SET lugar = '1A', no_serie = 'CS-TEST' WHERE id = %s", (ticket_id,))
        db_connection.commit()
        print_test_result("RI-1.1: Valid check-in (Change First class ticket to new first class seat)", "SUCCESS", "SUCCESS", counters)
    except psycopg2.Error as e:
        db_connection.rollback()
        print_test_result("RI-1.1: Valid check-in (Change First class ticket to new first class seat)", "SUCCESS", "FAILED", counters, str(e))

    # Test 2: Wrong class assignment
    # Create second class ticket
    db_query.execute("INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe) VALUES (1, %s, 'Test Passenger 2', 50.0, false) RETURNING id", (codigo_reserva,))
    ticket_id2 = db_query.fetchone()[0]
    db_connection.commit()

    try:
        db_query.execute("UPDATE bilhete SET lugar = '1B', no_serie = 'CS-TEST' WHERE id = %s", (ticket_id2,))
        db_connection.commit()
        print_test_result("RI-1.2: Wrong class assignment (economy ticket to first class seat)", "VIOLATION", "SUCCESS", counters)
    except psycopg2.Error as e:
        db_connection.rollback()
        if "Classe do bilhete" in str(e) or "O assento atribuído" in str(e):
            print_test_result("RI-1.2: Wrong class assignment (Assign first class seat to economy ticket)", "VIOLATION", "VIOLATION", counters)
        else:
            print_test_result("RI-1.2: Wrong class assignment (Assign first class seat to economy ticket)", "VIOLATION", "OTHER_ERROR", counters, str(e))

    # Test 3: Wrong airplane assignment
    # Create a second airplane
    db_query.execute("INSERT INTO aviao (no_serie, modelo) VALUES ('CS-WRONG', 'Wrong Aircraft')")
    db_query.execute("INSERT INTO assento (lugar, no_serie, prim_classe) VALUES ('1A', 'CS-WRONG', false)")
    db_connection.commit()

    try:
        db_query.execute("UPDATE bilhete SET lugar = '1A', no_serie = 'CS-WRONG' WHERE id = %s", (ticket_id2,))
        db_connection.commit()
        print_test_result("RI-1.3: Wrong airplane assignment", "VIOLATION", "SUCCESS", counters)
    except psycopg2.Error as e:
        db_connection.rollback()
        if "Classe do bilhete" in str(e) or "O assento atribuído" in str(e):
            print_test_result("RI-1.3: Wrong airplane assignment", "VIOLATION", "VIOLATION", counters)
        else:
            print_test_result("RI-1.3: Wrong airplane assignment", "VIOLATION", "OTHER_ERROR", counters, str(e))

    # Test 4: Update seat assignment
    db_query.execute("INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe) VALUES (1, %s, 'Test Passenger 3', 100.0, true) RETURNING id", (codigo_reserva,))
    ticket_id3 = db_query.fetchone()[0]
    db_connection.commit()

    try:
        db_query.execute("UPDATE bilhete SET lugar = '1A', no_serie = 'CS-TEST' WHERE id = %s", (ticket_id3,))
        db_connection.commit()
        print_test_result("RI-1.4: Update seat assignment", "SUCCESS", "SUCCESS", counters)
    except psycopg2.Error as e:
        db_connection.rollback()
        if "Classe do bilhete" in str(e) or "O assento atribuído" in str(e):
            print_test_result("RI-1.4: Update seat assignment", "VIOLATION", "VIOLATION", counters)
        else:
            print_test_result("RI-1.4: Update seat assignment", "VIOLATION", "OTHER_ERROR", counters, str(e))

def test_ri2_capacity_validation(db_query, db_connection, counters):
    """Test RI-2: Capacity validation"""
    print("=" * 60)
    print("TESTING RI-2: CAPACITY VALIDATION")
    print("=" * 60)

    # New sale for capacity testing
    sale_time = datetime.now() - timedelta(hours=1)
    db_query.execute("INSERT INTO venda (nif_cliente, balcao, hora) VALUES ('987654321', 'OPO', %s) RETURNING codigo_reserva", (sale_time,))
    codigo_reserva = db_query.fetchone()[0]
    db_connection.commit()

    # Test 1: Fill first class to capacity (2 seats available)
    for i in range(2):
        try:
            db_query.execute("INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe) VALUES (1, %s, %s, 150.0, true)", (codigo_reserva, f'First Class {i+1}'))
            db_connection.commit()
            print_test_result(f"RI-2.1.{i+1}: Valid first class ticket {i+1}/2", "SUCCESS", "SUCCESS", counters)
        except psycopg2.Error as e:
            db_connection.rollback()
            print_test_result(f"RI-2.1.{i+1}: Valid first class ticket {i+1}/2", "SUCCESS", "FAILED", counters, str(e))

    # Test 2: Try to exceed first class capacity
    try:
        db_query.execute("INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe) VALUES (1, %s, 'Overflow First', 150.0, true)", (codigo_reserva,))
        db_connection.commit()
        print_test_result("RI-2.2: First class capacity overflow", "VIOLATION", "SUCCESS", counters)
    except psycopg2.Error as e:
        db_connection.rollback()
        if "Excedida a capacidade de 1" in str(e):
            print_test_result("RI-2.2: First class capacity overflow", "VIOLATION", "VIOLATION", counters)
        else:
            print_test_result("RI-2.2: First class capacity overflow", "VIOLATION", "OTHER_ERROR", counters, str(e))

    # Test 3: Fill economy class to capacity (4 seats available)
    for i in range(4):
        try:
            db_query.execute("INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe) VALUES (1, %s, %s, 75.0, false)", (codigo_reserva, f'Economy {i+1}'))
            db_connection.commit()
            print_test_result(f"RI-2.3.{i+1}: Valid economy ticket {i+1}/4", "SUCCESS", "SUCCESS", counters)
        except psycopg2.Error as e:
            db_connection.rollback()
            print_test_result(f"RI-2.3.{i+1}: Valid economy ticket {i+1}/4", "SUCCESS", "FAILED", counters, str(e))

    # Test 4: Try to exceed economy capacity
    try:
        db_query.execute("INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe) VALUES (1, %s, 'Overflow Economy', 75.0, false)", (codigo_reserva,))
        db_connection.commit()
        print_test_result("RI-2.4: Economy class capacity overflow", "VIOLATION", "SUCCESS", counters)
    except psycopg2.Error as e:
        db_connection.rollback()
        if "Excedida a capacidade de 2" in str(e):
            print_test_result("RI-2.4: Economy class capacity overflow", "VIOLATION", "VIOLATION", counters)
        else:
            print_test_result("RI-2.4: Economy class capacity overflow", "VIOLATION", "OTHER_ERROR", counters, str(e))

def test_ri3_sale_time_validation(db_query, db_connection, counters):
    """Test RI-3: Sale time validation"""
    print("=" * 60)
    print("TESTING RI-3: SALE TIME VALIDATION")
    print("=" * 60)

    # Get flight departure time
    db_query.execute("SELECT hora_partida FROM voo WHERE id = 1")
    departure_time = db_query.fetchone()[0]

    # Test scenarios
    test_scenarios = [
        ("Valid: 1 hour before departure", departure_time - timedelta(hours=1), "SUCCESS"),
        ("Valid: 10 minutes before departure", departure_time - timedelta(minutes=10), "SUCCESS"),
        ("Invalid: At departure time", departure_time, "VIOLATION"),
        ("Invalid: 1 hour after departure", departure_time + timedelta(hours=1), "VIOLATION"),
        ("Invalid: 1 day after departure", departure_time + timedelta(days=1), "VIOLATION"),
    ]
    for i, (description, sale_time, expected) in enumerate(test_scenarios, 1):
        try:
            # Create sale
            db_query.execute("INSERT INTO venda (nif_cliente, balcao, hora) VALUES (%s, 'CDG', %s) RETURNING codigo_reserva", (f'11111111{i}', sale_time))
            codigo_reserva = db_query.fetchone()[0]
            # Try to add ticket
            db_query.execute("INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe) VALUES (1, %s, %s, 100.0, false)", (codigo_reserva, f'Test Sale {i}'))
            db_connection.commit()
            print_test_result(f"RI-3.{i}: {description}", expected, "SUCCESS", counters)
        except psycopg2.Error as e:
            db_connection.rollback()
            if "Hora da venda" in str(e):
                print_test_result(f"RI-3.{i}: {description}", expected, "VIOLATION", counters)
            else:
                print_test_result(f"RI-3.{i}: {description}", expected, "OTHER_ERROR", counters, str(e))

def cleanup_db(db_query, db_connection):
    """Cleans up all the data on the db."""
    print("Cleaning up test data...")
    db_query.execute("TRUNCATE TABLE bilhete, venda, voo, assento, aviao, aeroporto RESTART IDENTITY CASCADE")
    db_connection.commit()
    print("✓ Database cleanup complete\n")

def main():
    """Run all integrity constraint tests"""
    print("AVIACAO DATABASE INTEGRITY CONSTRAINT TESTING")
    print("=" * 60)
    print(f"Start time: {datetime.now()}")
    print()

    db_connection = psycopg2.connect(host='localhost', database='aviacao', user='postgres', password='postgres')
    db_query = db_connection.cursor()
    counters = {'passed': 0, 'failed': 0}

    try:
        setup_minimal_data(db_query, db_connection)
        test_ri1_checkin_validation(db_query, db_connection, counters)
        cleanup_db(db_query, db_connection)
        setup_minimal_data(db_query, db_connection)
        test_ri2_capacity_validation(db_query, db_connection, counters)
        cleanup_db(db_query, db_connection)
        setup_minimal_data(db_query, db_connection)
        test_ri3_sale_time_validation(db_query, db_connection, counters)
        cleanup_db(db_query, db_connection)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        counters['failed'] += 1

    finally:
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Passed: {counters['passed']}")
        print(f"Tests Failed: {counters['failed']}")
        print(f"Total Tests:  {counters['passed'] + counters['failed']}")
        print()
        print(f"End time: {datetime.now()}")

        db_query.close()
        db_connection.close()

if __name__ == "__main__":
    main()
