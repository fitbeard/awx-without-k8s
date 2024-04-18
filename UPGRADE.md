# Upgrade Postgres to v15 and fix AWX database migrations

## 1. Deprovision all AWX instances

```bash
# docker exec -ti awx-task bash
$ awx-manage list_instances
[default capacity=222 policy=100%]
  awx-1.demo.io capacity=57 node_type=hybrid version=24.2.0 heartbeat="2024-04-15 21:12:38"
  awx-2.demo.io capacity=57 node_type=hybrid version=24.2.0 heartbeat="2024-04-15 21:13:06"
  awx-receptor-1.demo.io capacity=27 node_type=execution version=ansible-runner-2.3.4 heartbeat="2024-04-15 21:13:01"
  awx-receptor-2.demo.io capacity=27 node_type=execution version=ansible-runner-2.3.4 heartbeat="2024-04-15 21:12:08"
  awx-receptor-3.demo.io capacity=27 node_type=execution version=ansible-runner-2.3.4 heartbeat="2024-04-15 21:12:21"
  awx-receptor-behind-hop-1.demo.io capacity=27 node_type=execution version=ansible-runner-2.3.4 heartbeat="2024-04-15 21:12:15"

[controlplane capacity=114 policy=100%]
  awx-1.demo.io capacity=57 node_type=hybrid version=24.2.0 heartbeat="2024-04-15 21:12:38"
  awx-2.demo.io capacity=57 node_type=hybrid version=24.2.0 heartbeat="2024-04-15 21:13:06"

[ungrouped capacity=0]
  awx-receptor-hop-1.demo.io node_type=hop heartbeat="2024-04-15 21:12:22"
```

```bash
awx-manage deprovision_instance --hostname=awx-receptor-1.demo.io
...
awx-manage deprovision_instance --hostname=XXXX
```

## 2. Backup and upgrade Postgres from v13 to v15

```bash
cd /opt/postgres
docker exec -it postgres pg_dumpall -U awx > dump.sql
docker-compose down
mv data data-v13-backup
mkdir data
# In 'docker-compose.yml' config change postgres image tag to '15'
docker-compose up -d
cat dump.sql | docker exec -it postgres pgsql -U awx
docker exec -ti postgres psql -U awx
# Change awx user password to trigger new host_auth_method. Can be same password as before.
awx=# \password
Enter new password for user "awx":
Enter it again:
awx=# exit
# Set 'awx_pg_is_on_supported_version' to 'true' and continue AWX upgrade as usual
```
