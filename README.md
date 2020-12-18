# awx-ha-cluster

[AWX](https://github.com/ansible/awx) is an upstream project of Ansible Tower. Commercial Ansible Tower comes with clustering functionality out of the box. More likely the same functionality can be achieved in AWX by tweaking few file modifications and settings. Ideas from  official Ansible Tower installation playbook and sub-reddits.

## AWX configuration and deployment

Compatible with AWX __16.0.0__
|Date|Change|
|---|---|
|2020 04 27|Updated to support AWX version __11.x__|
|2020 05 12|[Added support for Isolated nodes](/ISOLATED.md)|
|2020 08 27|Updated to support AWX version __14.x__|
|2020 12 18|Updated to support AWX version __16.x__|
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
ansible -i inventory/demo all -a "docker rmi awx_web_img_id awx_task_img_id"
```
