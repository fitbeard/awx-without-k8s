# Changelog

## [22.7.0](https://github.com/fitbeard/awx-without-k8s/compare/v22.5.0...v22.7.0) (2023-08-17)

### Features

* Updated to support AWX version `22.7.0`

### Improvements

* Make more Nginx params configurable
* Make more Uwsgi params configurable

## [22.5.0](https://github.com/fitbeard/awx-without-k8s/compare/v22.4.0...v22.5.0) (2023-07-25)

### Features

* Updated to support AWX version `22.5.0`

## [22.4.0](https://github.com/fitbeard/awx-without-k8s/compare/v22.2.0...v22.4.0) (2023-07-07)

### Features

* Updated to support AWX version `22.4.0`
* Renamed variables:

  `awx_receptor_ca_crt` to `awx_mesh_ca_crt`

  `awx_receptor_ca_key` to `awx_mesh_ca_key`

### Improvements

* Make workers uuids static
* Make Postgres keepalives options configurable

## [22.2.0](https://github.com/fitbeard/awx-without-k8s/compare/v22.0.0...v22.2.0) (2023-05-11)

### Features

* Updated to support AWX version `22.2.0`

## 22.0.0 (05 April, 2023)

FEATURES

* Updated to support AWX version `22.0.0`

## 21.14.0 (05 April, 2023)

FEATURES

* Updated to support AWX version `21.14.0`

IMPROVEMENTS

* Fix SELinux permission denied issue inside custom `awx-ee` container

## 21.13.0 (10 March, 2023)

FEATURES

* Updated to support AWX version `21.13.0`

## 21.12.0 (14 February, 2023)

FEATURES

* Updated to support AWX version `21.12.0`

## 21.11.0 (02 February, 2023)

FEATURES

* Updated to support AWX version `21.11.0`

IMPROVEMENTS

* Custom EE image is now available for both `linux/amd64` and `linux/arm64` architectures

* Starting with this release the code is only compatible with Ansible version 4.0.0 and above

* This code is now avaibale in an Ansible collection form.

  It can be installed with the command:

  `ansible-galaxy collection install fitbeard.awx`

  or

  `ansible-galaxy collection install fitbeard.awx:21.11.0`

## 21.10.2 (21 December, 2022)

FEATURES

* Updated to support AWX version `21.10.2`

## 21.9.0 (23 November, 2022)

FEATURES

* Updated to support AWX version `21.9.0`
* Added manual peering scenario (Ansible Automation Platform style)
* Added hop node support

IMPROVEMENTS

* Now new execution and hop nodes are added automatically during configuration

## 21.8.0 (04 November, 2022)

FEATURES

* Updated to support AWX version `21.8.0`

## 21.7.0 (21 October, 2022)

FEATURES

* Updated to support AWX version `21.7.0`

IMPROVEMENTS

* Total code refactoring

## 17.0 (08 February, 2021)

FEATURES

* Updated to support AWX version `17.x`

## 16.0 (18 December, 2020)

FEATURES

* Updated to support AWX version `16.x`

## 14.0 (27 December, 2020)

FEATURES

* Updated to support AWX version `14.x`

## 11.0 (27 April, 2020)

FEATURES

* Updated to support AWX version `11.x`
