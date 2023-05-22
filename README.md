# DatabaseAPI1
Python API that reads .fastq and .sam files into a PostgreSQL DB.
Current ERD: 
![three entity RD for postgres set up. seperate tables for data from fastq reads, sam files as well as kraken output together, and file_id table](images/postgresV1.png "ERD for postgresDB")

to start:  
1. start postgresql
2. run ```alembic init alembic```
3. ```alembic revision --autogenerate -m "New Migration"```
4. ```uvicorn main:app --reload```