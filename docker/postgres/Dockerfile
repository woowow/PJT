FROM postgres:14

ENV POSTGRES_DB=paper_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

COPY init.sql /docker-entrypoint-initdb.d/01_init.sql
COPY init_data.sql /docker-entrypoint-initdb.d/02_data.sql
