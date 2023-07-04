# DatabaseAPI1
Python API that reads .fastq and .sam files into three separate tables in a PostgreSQL DB.
Current ERD: 
![three entity RD for postgres set up. seperate tables for data from fastq reads, sam files as well as kraken output together, and file_id table](images/postgresV1.png "ERD for postgresDB")

to start:  
1. start postgresql
2. run ```alembic revision --autogenerate -m "New Migration"```
3. ```alembic upgrade head```
4. ```uvicorn main:app --reload --port 8080```
![screenshot of three entity postgres API](images/mainbranchendpoints.png "Screenshot of three entity postgres db API")
5. now with added get dimensions endpoints, but the returned response models are not good.
![screenshot of threedimensionendpoint](images/mainbranchthreedimensionscreenshot1.png "awful response format")
![screenshot of threedimensionendpoint2](images/mainbranchthreedimensionscreenshot2.png "really  awful")