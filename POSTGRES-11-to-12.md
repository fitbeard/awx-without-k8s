# Pre AWX v17 Postgres upgrade from 11 to 12

1. Stop all docker containers on all nodes

```bash
docker stop awx_web awx_task
```

2. Stop Postgres container

```bash
docker stop postgres
```

3. Create Postgres 12 data migration directory

```bash
mkdir /opt/postgres/data_v12 && mkdir /opt/postgres/data_v12/pgdata
```

4. Backup old Postgres data

```bash
cp -r /opt/postgres/data /opt/postgres/data.backup
```

5. Run Postgres upgrade container

```bash
docker run --rm \
      -v /opt/postgres/data/pgdata:/var/lib/postgresql/11/data \
      -v /opt/postgres/data_v12/pgdata:/var/lib/postgresql/12/data \
      -e PGUSER=awx -e POSTGRES_INITDB_ARGS="-U awx" \
      tianon/postgres-upgrade:11-to-12 --username=awx
```

6. Copy old pg_hba.conf

```bash
cp /opt/postgres/data/pgdata/pg_hba.conf /opt/postgres/data_v12/pgdata/pg_hba.conf
```

7. Remove old Postgres data and replace with updated

```bash
rm -fr /opt/postgres/data && mv /opt/postgres/data_v12 /opt/postgres/data
```
