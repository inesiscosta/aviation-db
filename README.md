# Aviacao Database & API Project

This project provides a ready-to-use environment for developing, testing, and analyzing an aviation database system. It includes:

- A **PostgreSQL** server with schema and initial data automatically loaded.
- A **Flask** REST API for interacting with the aviation database.
- A **Jupyter Notebook** environment for data analysis, exploration, and documentation.
- Scripts for data generation and database management.

## Project Overview

This repository is designed for rapid prototyping and experimentation with a relational aviation database. It enables you to:

- Define and enforce a relational schema with integrity constraints.
- Generate and import realistic aviation data.
- Develop and test RESTful endpoints using Flask.
- Analyze and visualize data using Jupyter Notebooks.
- Easily reset or reinitialize the database for clean testing.

The `aviacao.sql` file contains the schema and base data, and is automatically imported when the Postgres service starts.  
The included notebooks demonstrate queries, constraints, and indexes implemented in the system.

## Data Generation

The `data/generate_data.c` program generates a SQL file (`populate.sql`) containing synthetic aviation data. You can use this file to populate the database with realistic test data by either:

- Placing `populate.sql` in the `docker-entrypoint-initdb.d/` directory (for automatic import), or
- Importing it manually into your PostgreSQL instance.

**Generated data includes:**

- **Airports:**  
  - At least 10 real international airports in Europe  
  - At least 2 cities with 2 airports each

- **Airplanes:**  
  - At least 10 real airplanes  
  - 3+ distinct models  
  - Realistic seat counts  
  - Approximately 10% first-class rows

- **Flights:**  
  - At least 5 flights per day from January 1 to July 31, 2025  
  - Coverage of all airports and airplanes  
  - Round-trip flights  
  - Consistent airplane scheduling

- **Tickets:**  
  - At least 30,000 tickets sold (from 10,000+ sales)  
  - All past flights have check-ins  
  - Both first and second class tickets sold for every flight

## How to Use

### 1. Clone the Project

```sh
git clone <repo-url>
cd <project-folder>
```

### 4. Initialize or Reset the Database

```sh
./setup.sh
```

### 3. Start the Services

```sh
./run.sh
```

### **Credits:**  
This project is based on the assignment and starter code provided by the Databases course instructors at Instituto Superior Técnico (IST). Special thanks to the teaching staff for their materials, guidance, and support.

Copyright (c) BDist Development Team  
Distributed under the terms of the Modified BSD License.