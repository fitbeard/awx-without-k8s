# awx-without-k8s

[AWX](https://github.com/ansible/awx) is originally designed to run
in a Kubernetes environment only.
This code allows you to install and use AWX only using Docker without K8S.
Ideas from [awx](https://github.com/ansible/awx), [awx-operator](https://github.com/ansible/awx-operator)
and [awx-ee](https://github.com/ansible/awx-ee) code.

## AWX configuration and deployment

Main branch is compatible with AWX version __24.2.0__.
Use git tag with desired version.

[`CHANGELOG`](./CHANGELOG.md)

This code can also be used as an Ansible collection and installed from Ansible Galaxy:

```shell
ansible-galaxy collection install fitbeard.awx
```

or desired version

```shell
ansible-galaxy collection install fitbeard.awx:24.2.0
```

## Dependencies

- Ansible
- Working hostname resolution mechanism
(DNS records, Docker's `extra_hosts` values, `/etc/hosts`)

### Install demo

Befor installation please read about AWX in general,
AWX node types (control, hybrid, hop, execution),
[execution nodes](https://github.com/ansible/awx/blob/devel/docs/execution_nodes.md)
and [receptor](https://github.com/ansible/receptor).
___These are beyond the scope of this guide.___

Demo secrets, certs, keys are for test purpose ___ONLY___. Please do not use for production.

#### Create secret data first

This is not necessary as this demo contains all needed secrets.
This is an example of how to create secret data for production.

```bash
mkdir secrets
cd secrets
```

##### 1. Create AWX CA

```bash
openssl genrsa -out awx_receptor_signing_private_key 4096
openssl rsa -in awx_receptor_signing_private_key -out awx_receptor_signing_public_key -outform PEM -pubout

openssl genrsa -out awx_mesh_ca_key 4096
openssl req -x509 -new -nodes -key awx_mesh_ca_key -subj "CN=AWX Demo Receptor Root CA" -sha256 -days 3650 -out awx_mesh_ca_crt
```

##### 2. Create self-signed SSL for AWX web

```bash
openssl req -x509 -newkey rsa:4096 -keyout awx_web_cert_key -out awx_web_cert_crt -sha256 -days 365
openssl rsa -in awx_web_cert_key -out awx_web_cert_key
```

##### 3. Create receptor signing key pair

```bash
openssl genrsa -out awx_receptor_signing_private_key 4096
openssl rsa -in awx_receptor_signing_private_key -out awx_receptor_signing_public_key -outform PEM -pubout
```

##### 4. Create receptor key pair

Repeat for every node in cluster

```bash
docker pull quay.io/ansible/receptor:latest
export receptor_hostname=awx-1.demo.io
docker run --rm -v $PWD:/tmp --env-file <(env | grep receptor_hostname) quay.io/ansible/receptor:latest receptor --cert-makereq bits=2048 commonname=$receptor_hostname dnsname=$receptor_hostname nodeid=$receptor_hostname outreq=/tmp/$receptor_hostname.req outkey=/tmp/$receptor_hostname.key
docker run --rm -v $PWD:/tmp --env-file <(env | grep receptor_hostname) quay.io/ansible/receptor:latest receptor --cert-signreq req=/tmp/$receptor_hostname.req cacert=/tmp/awx_mesh_ca_crt cakey=/tmp/awx_mesh_ca_key notbefore=$(date --iso-8601=seconds) notafter=$(date --date="+2 years" --iso-8601=seconds) outcert=/tmp/$receptor_hostname.crt verify=yes
```

#### Modify `awx_ee_image_url` variable

Create [`custom Docker image`](./docker/Dockerfile.awx-ee) for execution nodes and for management nodes (if `awx_node_role_type` variable is set to `hybrid`).

Or use `quay.io/tadas/awx-without-k8s-ee:latest` image which is based on the [`same Dockerfile`](./docker/Dockerfile.awx-ee).

#### Start installation

Before actually running playbook, take a look at the role defaults, `demo/inventory` and `demo/host_vars|group_vars` and make changes accordingly.

```bash
cd ../demo
ansible-playbook -i inventory demo.yml --diff
```

#### Add execution nodes to the AWX cluster (manually)

Ansible will do it automatically but in case you need re-add it again.

Repeat for every execution node in cluster

This can be done in Web UI or by using `awx-manage` CLI (partially):

```bash
docker exec -ti awx-task bash
awx-manage provision_instance --hostname=awx-receptor-1.demo.io --node_type=execution
```

<img width="936" src="https://github.com/fitbeard/awx-without-k8s/assets/18698204/176cb25a-44e1-4f13-870a-8dbf0954dbc8" alt="Topology" />

### Upgrade

```bash
cd demo
ansible-playbook -i inventory demo.yml --diff -e awx_tasks=upgrade
```

### Remove old Docker images

```bash
cd demo
ansible -i inventory all -a "docker rmi awx_img_id"
```

## Contributing

You'll need to make sure that you have [`pre-commit`](https://pre-commit.com)
setup and installed in your environment by running these commands:

```console
pre-commit install --hook-type commit-msg
````
