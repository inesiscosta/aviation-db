# Aviacao Database & API Project

This project provides a ready-to-use environment for developing, testing, and analyzing an aviation database system. It includes:

- A **PostgreSQL** server with schema and initial data automatically loaded.
- A **Flask** REST API for interacting with the aviation database.
- A **Jupyter Notebook** environment for data analysis, exploration, and documentation.
- Scripts for data generation and database management.

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

## Project Overview

This repository is designed for rapid prototyping and experimentation with a relational aviation database. It enables you to:

- Define and enforce a relational schema with integrity constraints.
- Generate and import realistic aviation data.
- Develop and test RESTful endpoints using Flask.
- Analyze and visualize data using Jupyter Notebooks.
- Easily reset or reinitialize the database for clean testing.

The `aviacao.sql` file contains the schema and base data, and is automatically imported when the Postgres service starts.  
The included notebooks demonstrate queries, constraints, and indexes implemented in the system.

## Useful Scripts

- **generate_data.c**: Generates synthetic data to populate the database.
- **setup.sh**: Initializes or resets the database (with optional clean/reimport).
- **run.sh**: Starts all required services.


### **Credits:**  
This project is based on the assignment and starter code provided by the Databases course instructors at Instituto Superior Técnico (IST). Special thanks to the teaching staff for their materials, guidance, and support.

Copyright (c) BDist Development Team  
Distributed under the terms of the Modified BSD License.