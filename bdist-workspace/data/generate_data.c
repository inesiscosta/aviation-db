#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdbool.h>

#define MAX_AIRPORTS 20
#define MAX_MODELS 6
#define MAX_AIRPLANES 20
#define MAX_SEATS_PER_AIRPLANE 250
#define MAX_FLIGHTS 18000
#define MAX_SALES 1600000
#define MAX_TICKETS 3200000
#define MAX_NAME_LEN 100
#define SEAT_LETTERS "ABCDEF"
#define SEATS_PER_ROW 6
#define MAX_FLIGHT_KEYS 18000

typedef struct {
    char dep_time[20];
    char partida[8];
    char chegada[8];
} FlightKey;

int used_keys_count = 0;

typedef struct Model {
    char name[32];
    int total_seats;
} Model;

typedef struct Airport {
    char iata_code[8];
    char name[64];
    char city[64];
    char country[64];
} Airport;

typedef struct Airplane Airplane;
typedef struct Seat {
    char id[4];
    bool first_class;
    Airplane* airplane;
} Seat;

struct Airplane {
    char serial_no[16];
    Model* model;
    Seat seats[MAX_SEATS_PER_AIRPLANE];
};

typedef struct Flight {
    Airplane* airplane;
    Airport* departure_airport;
    struct tm departure_datetime;
    Airport* arrival_airport;
    struct tm arrival_datetime;
} Flight;

typedef struct Sale {
    char nif[16];
    struct tm datetime;
    Airport* retail_counter;
} Sale;

typedef struct Ticket {
    Flight* flight;
    char name[MAX_NAME_LEN];
    float price;
    Seat* seat;
    bool first_class;
    Sale* sale;
} Ticket;

typedef struct FlightInfo {
    char departure_city[64];
    char arrival_city[64];
    int flight_time;
    float price_2c;
    float price_1c;
} FlightInfo;

Airport airports[MAX_AIRPORTS] = {
    {"VIE", "Vienna Intl", "Vienna", "Austria"},
    {"PRG", "Václav Havel", "Prague", "Czech Republic"},
    {"CPH", "Kastrup", "Copenhagen", "Denmark"},
    {"CDG", "Paris Charles de Gaulle", "Paris", "France"},
    {"ORY", "Paris Orly", "Paris", "France"},
    {"MUC", "Munich", "Munich", "Germany"},
    {"FCO", "Fiumicino", "Rome", "Italy"},
    {"LIN", "Linate", "Milan", "Italy"},
    {"MXP", "Malpensa", "Milan", "Italy"},
    {"AMS", "Schiphol", "Amsterdam", "Netherlands"},
    {"LIS", "Humberto Delgado", "Lisboa", "Portugal"},
    {"OPO", "Francisco Sá Carneiro", "Porto", "Portugal"},
    {"BCN", "El Prat", "Barcelona", "Spain"},
    {"MAD", "Barajas", "Madrid", "Spain"},
    {"ZRH", "Zurich", "Zurich", "Switzerland"},
    {"IST", "Istanbul Airport", "Istanbul", "Türkiye"},
    {"SAW", "Sabiha Gökçen", "Istanbul", "Türkiye"},
    {"LGW", "Gatwick", "London", "United Kingdom"},
    {"LHR", "Heathrow", "London", "United Kingdom"},
    {"STN", "Stansted", "London", "United Kingdom"}
};
int airports_count = 20;

Model models[MAX_MODELS] = {
    {"A220-300", 145},
    {"B737-800", 160},
    {"A320", 186},
    {"B737 MAX 8", 189},
    {"A321", 244},
    {"B787-8", 242}
};
int models_count = 6;

const char* country_prefixes[] = {"CS", "D", "G", "F", "I", "OE", "EC", "PH", "HB"};
#define COUNTRY_PREFIXES_COUNT (sizeof(country_prefixes)/sizeof(country_prefixes[0]))

Airplane airplanes[MAX_AIRPLANES * sizeof(Airplane)];
int airplanes_count = 20;

const char* first_names[] = {
    "Miguel", "Ana", "João", "Maria", "David", "Sara", "Pedro", "Inês", "Tiago", "Rita",
    "Lucas", "Leonor", "Francisco", "Matilde", "Gonçalo", "Beatriz", "André", "Carolina", "Diogo", "Margarida",
    "Bruno", "Sofia", "Ricardo", "Mariana", "Rafael", "Catarina", "Alexandre", "Lara", "Daniel", "Filipa",
    "Hugo", "Patrícia", "Fábio", "Raquel", "Carlos", "Teresa", "Eduardo", "Helena", "Samuel", "Cláudia",
    "Jorge", "Susana", "Paulo", "Vera", "Manuel", "Diana", "Artur", "Isabel", "António", "Eva"
};
const char* last_names[] = {
    "Silva", "Santos", "Ferreira", "Pereira", "Oliveira", "Costa", "Rodrigues", "Martins", "Jesus", "Sousa",
    "Fernandes", "Gonçalves", "Gomes", "Lopes", "Marques", "Alves", "Almeida", "Ribeiro", "Pinto", "Carvalho",
    "Teixeira", "Moreira", "Correia", "Mendes", "Nunes", "Soares", "Vieira", "Monteiro", "Cardoso", "Rocha",
    "Cruz", "Neves", "Coelho", "Reis", "Freitas", "Figueiredo", "Machado", "Barbosa", "Campos", "Simões",
    "Azevedo", "Fonseca", "Batista", "Borges", "Dias", "Castro", "Raposo", "Henriques", "Moura", "Pires",
};
#define FIRST_NAMES_COUNT (sizeof(first_names)/sizeof(first_names[0]))
#define LAST_NAMES_COUNT (sizeof(last_names)/sizeof(last_names[0]))

void random_full_name(char* buf, size_t buflen) {
    int first_idx = rand() % FIRST_NAMES_COUNT;
    int last_idx = rand() % LAST_NAMES_COUNT;
    snprintf(buf, buflen, "%s %s", first_names[first_idx], last_names[last_idx]);
}

void format_datetime(struct tm* dt, char* buf, size_t bufsize) {
    strftime(buf, bufsize, "%Y-%m-%d %H:%M:%S", dt);
}

void add_minutes(struct tm* date, int minutes) {
    time_t t = mktime(date);
    t += minutes * 60;
    *date = *localtime(&t);
}

void add_days(struct tm* date, int days) {
    time_t t = mktime(date);
    t += days * 24 * 3600;
    *date = *localtime(&t);
}

void shuffle_ints(int* array, int n) {
    for (int i = n - 1; i > 0; --i) {
        int j = rand() % (i + 1);
        int tmp = array[i];
        array[i] = array[j];
        array[j] = tmp;
    }
}

int flight_key_exists(const char* dep_time, const char* partida, const char* chegada, FlightKey *used_keys) {
    for (int i = 0; i < used_keys_count; ++i) {
        if (strcmp(used_keys[i].dep_time, dep_time) == 0 &&
            strcmp(used_keys[i].partida, partida) == 0 &&
            strcmp(used_keys[i].chegada, chegada) == 0) {
            return 1;
        }
    }
    return 0;
}

// Helper to add a key
void add_flight_key(const char* dep_time, const char* partida, const char* chegada, FlightKey *used_keys) {
    strcpy(used_keys[used_keys_count].dep_time, dep_time);
    strcpy(used_keys[used_keys_count].partida, partida);
    strcpy(used_keys[used_keys_count].chegada, chegada);
    used_keys_count++;
}

FlightInfo flight_infos[MAX_AIRPORTS * MAX_AIRPORTS];
int flight_infos_count = 0;

void generate_flight_infos() {
    for (int i = 0; i < airports_count; ++i) {
        for (int j = 0; j < airports_count; ++j) {
            if (i == j) continue;
            if (strcmp(airports[i].city, airports[j].city) == 0) continue;
            bool exists = false;
            for (int k = 0; k < flight_infos_count; ++k) {
                if (strcmp(flight_infos[k].departure_city, airports[i].city) == 0 &&
                    strcmp(flight_infos[k].arrival_city, airports[j].city) == 0) {
                    exists = true;
                    break;
                }
            }
            if (exists) continue;
            int base_minutes = 60 + rand() % (210 - 60 + 1);
            float base_price_2c = (float)(80 + rand() % (350 - 80 + 1)) + 0.99f;
            float base_price_1c = (float)((int)((base_price_2c * 1.4f) * 100 + 0.5)) / 100.0f;
            strcpy(flight_infos[flight_infos_count].departure_city, airports[i].city);
            strcpy(flight_infos[flight_infos_count].arrival_city, airports[j].city);
            flight_infos[flight_infos_count].flight_time = base_minutes;
            flight_infos[flight_infos_count].price_2c = base_price_2c;
            flight_infos[flight_infos_count].price_1c = base_price_1c;
            flight_infos_count++;
        }
    }
}

FlightInfo* find_flight_info(const char* dep_city, const char* arr_city) {
    for (int i = 0; i < flight_infos_count; ++i)
        if (strcmp(flight_infos[i].departure_city, dep_city) == 0 &&
            strcmp(flight_infos[i].arrival_city, arr_city) == 0)
            return &flight_infos[i];
    return NULL;
}

int main() {
    FlightKey *used_keys = malloc(MAX_FLIGHT_KEYS * sizeof(FlightKey));

    Flight* flights = malloc(MAX_FLIGHTS * sizeof(Flight));
    int flights_count = 0;

    Sale* sales = malloc(MAX_SALES * sizeof(Sale));
    int sales_count = 0;

    Ticket* tickets = malloc(MAX_TICKETS * sizeof(Ticket));
    int tickets_count = 0;
    srand((unsigned int)time(NULL));
    FILE* sql_file = fopen("populate1.sql", "w");
    if (!sql_file) { perror("open populate1.sql"); return 1; }

    // --- Generate Airports ---
    for (int i = 0; i < airports_count; ++i) {
      fprintf(sql_file,
        "INSERT INTO aeroporto (codigo, nome, cidade, pais) VALUES ('%s', '%s', '%s', '%s');\n",
        airports[i].iata_code,
        airports[i].name,
        airports[i].city,
        airports[i].country
      );
    }

    int used_serials[MAX_AIRPLANES * 10] = {0};
    int used_serials_count = 0;
    for (int i = 0; i < airplanes_count; ++i) {
        int model_idx = rand() % models_count;
        airplanes[i].model = &models[model_idx];
        char serial_no[16];
        int unique = 0;
        while (!unique) {
            const char* prefix = country_prefixes[rand() % COUNTRY_PREFIXES_COUNT];
            char manufacturer_letter = airplanes[i].model->name[0];
            int number = 1000 + rand() % 9000;
            snprintf(serial_no, sizeof(serial_no), "%s-%c%d", prefix, manufacturer_letter, number);
            unique = 1;
            for (int j = 0; j < i; ++j) {
                if (strcmp(airplanes[j].serial_no, serial_no) == 0) {
                    unique = 0;
                    break;
                }
            }
        }
        strcpy(airplanes[i].serial_no, serial_no);
        fprintf(sql_file, "INSERT INTO aviao (no_serie, modelo) VALUES ('%s', '%s');\n",
            airplanes[i].serial_no, airplanes[i].model->name);

        int total_seats = airplanes[i].model->total_seats;
        int total_rows = (total_seats + SEATS_PER_ROW - 1) / SEATS_PER_ROW;
        int first_class_rows = (int)(total_rows * 0.1);
        for (int j = 0; j < total_seats; ++j) {
            int row_number = j / SEATS_PER_ROW + 1;
            char col_letter = SEAT_LETTERS[j % SEATS_PER_ROW];
            snprintf(airplanes[i].seats[j].id, sizeof(airplanes[i].seats[j].id), "%d%c", row_number, col_letter);
            airplanes[i].seats[j].first_class = row_number <= first_class_rows;
            airplanes[i].seats[j].airplane = &airplanes[i];
            // Write seat SQL
            fprintf(sql_file,
                "INSERT INTO assento (lugar, no_serie, prim_classe) VALUES ('%s', '%s', %s);\n",
                airplanes[i].seats[j].id,
                airplanes[i].serial_no,
                airplanes[i].seats[j].first_class ? "true" : "false"
            );
        }
    }

    generate_flight_infos();

    struct tm start_date = {0}, end_date = {0};
    start_date.tm_year = 2025 - 1900;
    start_date.tm_mon = 0;  // January
    start_date.tm_mday = 1;
    end_date.tm_year = 2025 - 1900;
    end_date.tm_mon = 6;    // July
    end_date.tm_mday = 31;
    int days = (int)((mktime(&end_date) - mktime(&start_date)) / (24 * 3600)) + 1;

    struct tm date = start_date;
    printf("Number of days: %d\n", days);
    for (int day = 0; day < days; ++day) {
        int airplane_indices[MAX_AIRPLANES];
        for (int i = 0; i < airplanes_count; ++i) airplane_indices[i] = i;
        shuffle_ints(airplane_indices, airplanes_count);
        for (int a = 0; a < airplanes_count; ++a) {
            Airplane* airplane = &airplanes[airplane_indices[a]];
            for (int interval = 0; interval < 2; ++interval) {
                int interval_start = interval == 0 ? 5 : 17;
                int interval_end = interval == 0 ? 8 : 20;
                int dep_idx, arr_idx;
                Airport *departure_airport, *arrival_airport;
                struct tm departure_time;
                char dep_buf[20];
                dep_idx = rand() % airports_count;
                departure_airport = &airports[dep_idx];
                do {
                    arr_idx = rand() % airports_count;
                } while (arr_idx == dep_idx || strcmp(airports[arr_idx].city, departure_airport->city) == 0);
                arrival_airport = &airports[arr_idx];
                departure_time = date;
                do {
                    int dep_hour = interval_start + rand() % (interval_end - interval_start + 1);
                    departure_time.tm_hour = dep_hour;
                    departure_time.tm_min = rand() % 60;
                    departure_time.tm_sec = 0;
                    format_datetime(&departure_time, dep_buf, sizeof(dep_buf));
                } while (flight_key_exists(dep_buf, departure_airport->iata_code, arrival_airport->iata_code, used_keys));
                add_flight_key(dep_buf, departure_airport->iata_code, arrival_airport->iata_code, used_keys);
                FlightInfo* info = find_flight_info(departure_airport->city, arrival_airport->city);
                int flight_minutes = info ? info->flight_time : 90;
                struct tm arrival_time = departure_time;
                add_minutes(&arrival_time, flight_minutes);
                Flight* flight = &flights[flights_count++];
                flight->airplane = airplane;
                flight->departure_airport = departure_airport;
                flight->arrival_airport = arrival_airport;
                flight->departure_datetime = departure_time;
                flight->arrival_datetime = arrival_time;
                char arr_buf[20];
                format_datetime(&departure_time, dep_buf, sizeof(dep_buf));
                format_datetime(&arrival_time, arr_buf, sizeof(arr_buf));
                fprintf(sql_file, "INSERT INTO voo (no_serie, hora_partida, hora_chegada, partida, chegada) VALUES ('%s', '%s', '%s', '%s', '%s');\n",
                    airplane->serial_no, dep_buf, arr_buf, departure_airport->iata_code, arrival_airport->iata_code);
                char ret_dep_buf[20], ret_arr_buf[20];
                struct tm return_departure;
                do {
                    return_departure = arrival_time;
                    add_minutes(&return_departure, 30 + rand() % 61);
                    format_datetime(&return_departure, ret_dep_buf, sizeof(ret_dep_buf));
                } while (flight_key_exists(ret_dep_buf, arrival_airport->iata_code, departure_airport->iata_code, used_keys));
                add_flight_key(ret_dep_buf, arrival_airport->iata_code, departure_airport->iata_code, used_keys);
                FlightInfo* ret_info = find_flight_info(arrival_airport->city, departure_airport->city);
                int ret_minutes = ret_info->flight_time;
                struct tm return_arrival = return_departure;
                add_minutes(&return_arrival, ret_minutes);
                Flight* return_flight = &flights[flights_count++];
                return_flight->airplane = airplane;
                return_flight->departure_airport = arrival_airport;
                return_flight->arrival_airport = departure_airport;
                return_flight->departure_datetime = return_departure;
                return_flight->arrival_datetime = return_arrival;
                format_datetime(&return_arrival, ret_arr_buf, sizeof(ret_arr_buf));
                fprintf(sql_file, "INSERT INTO voo (no_serie, hora_partida, hora_chegada, partida, chegada) VALUES ('%s', '%s', '%s', '%s', '%s');\n",
                    airplane->serial_no, ret_dep_buf, ret_arr_buf, arrival_airport->iata_code, departure_airport->iata_code);
            }
        }
        add_days(&date, 1);
    }

    bool model_used[MAX_MODELS] = {0};
    for (int i = 0; i < airplanes_count; ++i) {
      for (int m = 0; m < models_count; ++m) {
        if (strcmp(airplanes[i].model->name, models[m].name) == 0) {
          model_used[m] = true;
          break;
        }
      }
    }
    bool all_models_used = true;
    for (int m = 0; m < models_count; ++m) {
      if (!model_used[m]) {
        all_models_used = false;
        break;
      }
    }
    printf("All models used: %s\n", all_models_used ? "true" : "false");

    bool airport_visited[MAX_AIRPORTS] = {0};
    for (int i = 0; i < flights_count; ++i) {
      for (int a = 0; a < airports_count; ++a) {
        if (flights[i].departure_airport == &airports[a] || flights[i].arrival_airport == &airports[a]) {
          airport_visited[a] = true;
        }
      }
    }
    bool all_airports_visited = true;
    for (int a = 0; a < airports_count; ++a) {
      if (!airport_visited[a]) {
        all_airports_visited = false;
        break;
      }
    }
    printf("All airports visited: %s\n", all_airports_visited ? "true" : "false");

    bool airplane_used[MAX_AIRPLANES] = {0};
    for (int i = 0; i < flights_count; ++i) {
      for (int a = 0; a < airplanes_count; ++a) {
        if (flights[i].airplane == &airplanes[a]) {
          airplane_used[a] = true;
        }
      }
    }
    bool all_airplanes_used = true;
    for (int a = 0; a < airplanes_count; ++a) {
      if (!airplane_used[a]) {
        all_airplanes_used = false;
        break;
      }
    }
    printf("All airplanes used: %s\n", all_airplanes_used ? "true" : "false");

    for (int flight_id = 0; flight_id < flights_count; ++flight_id) {
        Flight* flight = &flights[flight_id];
        int total_seats = flight->airplane->model->total_seats;
        float occupancy = (rand() % 16 + 85) / 100.0f; // 85% to 100%
        int num_tickets_to_sell = (int)(total_seats * occupancy);

        int fc_indices[MAX_SEATS_PER_AIRPLANE], sc_indices[MAX_SEATS_PER_AIRPLANE];
        int fc_count = 0, sc_count = 0;
        for (int i = 0; i < total_seats; ++i) {
            if (flight->airplane->seats[i].first_class)
                fc_indices[fc_count++] = i;
            else
                sc_indices[sc_count++] = i;
        }

        while (num_tickets_to_sell > 0) {
            Sale* sale = &sales[sales_count++];
            snprintf(sale->nif, sizeof(sale->nif), "%09d", 100000000 + rand() % 900000000);
            sale->retail_counter = (rand() % 10 < 6) ? &airports[rand() % airports_count] : NULL;
            struct tm sale_time = flight->departure_datetime;
            int days_before = 1 + rand() % 90;
            int hours_before = rand() % 24;
            int mins_before = rand() % 60;
            sale_time.tm_mday -= days_before;
            sale_time.tm_hour -= hours_before;
            sale_time.tm_min -= mins_before;
            mktime(&sale_time);
            sale->datetime = sale_time;

            int num_sold_tickets = 1 + rand() % 5;
            if (num_sold_tickets > num_tickets_to_sell)
                num_sold_tickets = num_tickets_to_sell;

            char used_names[5][MAX_NAME_LEN];
            int used_name_count = 0;

            for (int t = 0; t < num_sold_tickets; ++t) {
                Ticket* ticket = &tickets[tickets_count++];
                ticket->flight = flight;
                ticket->sale = sale;

                bool first_class;
                if (fc_count && sc_count)
                    first_class = rand() % 2;
                else if (fc_count)
                    first_class = true;
                else
                    first_class = false;

                do {
                    random_full_name(ticket->name, MAX_NAME_LEN);
                    int unique = 1;
                    for (int n = 0; n < used_name_count; ++n) {
                        if (strcmp(used_names[n], ticket->name) == 0) {
                            unique = 0;
                            break;
                        }
                    }
                    if (unique) {
                        strcpy(used_names[used_name_count++], ticket->name);
                        break;
                    }
                } while (1);

                if (first_class && fc_count > 0) {
                    int idx = fc_indices[--fc_count];
                    ticket->seat = &flight->airplane->seats[idx];
                    FlightInfo* info = find_flight_info(flight->departure_airport->city, flight->arrival_airport->city);
                    ticket->price = info ? info->price_1c : 200.0f;
                } else if (sc_count > 0) {
                    int idx = sc_indices[--sc_count];
                    ticket->seat = &flight->airplane->seats[idx];
                    FlightInfo* info = find_flight_info(flight->departure_airport->city, flight->arrival_airport->city);
                    ticket->price = info ? info->price_2c : 100.0f;
                }
                ticket->first_class = first_class;
            }
            num_tickets_to_sell -= num_sold_tickets;
        }
    }
    for (int i = 0; i < sales_count; ++i) {
        char sale_time_buf[20];
        format_datetime(&sales[i].datetime, sale_time_buf, sizeof(sale_time_buf));
        if (sales[i].retail_counter) {
          fprintf(sql_file, "INSERT INTO venda (nif_cliente, balcao, hora) VALUES ('%s', '%s', '%s');\n",
            sales[i].nif,
            sales[i].retail_counter->iata_code,
            sale_time_buf
          );
        } else {
          fprintf(sql_file, "INSERT INTO venda (nif_cliente, balcao, hora) VALUES ('%s', NULL, '%s');\n",
            sales[i].nif,
            sale_time_buf
          );
        }
    }
    for (int i = 0; i < tickets_count; ++i) {
        int flight_id = tickets[i].flight - flights + 1;
        int sale_id = tickets[i].sale - sales + 1;
        fprintf(sql_file, "INSERT INTO bilhete (voo_id, codigo_reserva, nome_passegeiro, preco, prim_classe, lugar, no_serie) VALUES (%d, %d, '%s', %.2f, %s, '%s', '%s');\n",
            flight_id,
            sale_id,
            tickets[i].name,
            tickets[i].price,
            tickets[i].first_class ? "true" : "false",
            tickets[i].seat->id,
            tickets[i].flight->airplane->serial_no
        );
    }

    fclose(sql_file);
    printf("SQL data generated in populate.sql\n");
    free(used_keys);
    free(flights);
    free(sales);
    free(tickets);
    return 0;
}
