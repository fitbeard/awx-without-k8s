# awx-ha-cluster

[AWX](https://github.com/ansible/awx) is an upstream project of Ansible Tower. Commercial Ansible Tower comes with clustering functionality out of the box. More likely the same functionality can be achieved in AWX by tweaking few file modifications and settings. Ideas from  official Ansible Tower installation playbook and sub-reddits.

## AWX configuration and deployment

|Date|Change|
|---|---|
|2020 04 27|Updated to support AWX version __11+__|
|2020 05 12|[Added support for Isolated nodes](/ISOLATED.md)|

## Dependencies

- CentOS 7
- EPEL
- Ansible 2.8+
- Python `hvac` module (for HashiCorp Vault)

### Install

```bash
ansible-playbook -i inventory/demo -e @vars/demo.yml -e task=setup awx.yml
ansible-playbook -i inventory/demo -e @vars/demo.yml -e task=run awx.yml --skip-tags awx
ansible-playbook -i inventory/demo -e @vars/demo.yml -e task=run --tags awx --limit primary_awx_node awx.yml
ansible-playbook -i inventory/demo -e @vars/demo.yml awx.yml
```

### Upgrade

```bash
ansible-playbook -i inventory/demo -e @vars/demo.yml -e task=setup --tags awx awx.yml
ansible-playbook -i inventory/demo -e @vars/demo.yml -e task=upgrade --tags awx awx.yml
ansible-playbook -i inventory/demo -e @vars/demo.yml --tags awx awx.yml
```

### Remove old Docker images

```bash
ansible -i inventory/demo all -a "docker rmi awx_web_img_id awx_task_img_id"
```
