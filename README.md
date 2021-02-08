# awx-ha-cluster

[AWX](https://github.com/ansible/awx) is an upstream project of Ansible Tower. Commercial Ansible Tower comes with clustering functionality out of the box. More likely the same functionality can be achieved in AWX by tweaking few file modifications and settings. Ideas from  official Ansible Tower installation playbook and sub-reddits.

## AWX configuration and deployment

Master branch compatible with AWX __17.0.1__ Use git tag with desired version.
|Date|Change|
|---|---|
|2021 02 08|Updated to support AWX version __17.x__ [You must upgrade to Postgres 12 before this version](/POSTGRES-11-to-12.md)|
|2020 12 18|Updated to support AWX version __16.x__|
|2020 08 27|Updated to support AWX version __14.x__|
|2020 05 12|[Added support for Isolated nodes](/ISOLATED.md)|
|2020 04 27|Updated to support AWX version __11.x__|
After upgrading from previous version (__11.x__) remove memcached containers. They are not needed anymore.

## Dependencies

- CentOS 7
- EPEL
- Ansible 2.9+
- Python `hvac` module (for HashiCorp Vault)

### Install

```bash
ansible-playbook -i inventory/demo -e task=setup awx.yml --diff
ansible-playbook -i inventory/demo -e task=run awx.yml --skip-tags awx --diff
ansible-playbook -i inventory/demo -e task=run --tags awx --limit primary_awx_node awx.yml --diff
ansible-playbook -i inventory/demo awx.yml --diff
```

### Upgrade

```bash
ansible-playbook -i inventory/demo -e task=setup --tags awx awx.yml --diff
ansible-playbook -i inventory/demo -e task=upgrade --tags awx awx.yml --diff
ansible-playbook -i inventory/demo --tags awx awx.yml --diff
```

### Remove old Docker images

```bash
ansible -i inventory/demo all -a "docker rmi awx_img_id"
```
