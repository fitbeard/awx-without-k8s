#!/usr/bin/python
# coding: utf-8 -*-
# Copyright: (c) 2024, Martin Slemr <@slemrmartin>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: service
author: Martin Slemr (@slemrmartin)
short_description: Configure a gateway service.
description:
    - Configure an automation platform gateway service.
    - Their gateway API paths have prefixes of either / in case of gateway or /api/ otherwise
options:
    name:
      required: true
      type: str
      description: The name of the Service, must be unique
    new_name:
      type: str
      description: Setting this option will change the existing name (looked up via the name field)
    description:
      description: The description of the Service
      type: str
    api_slug:
      description:
      - URL slug for the gateway API path for the Controller, Hub and EDA services
      - Gateway API route requires value "gateway", but the slug is not used
      type: str
    http_port:
      description:
      - Name or ID referencing the Http Port
      - Required when creating a new route
      type: str
    service_cluster:
      description:
      - Name or ID referencing the Service Cluster
      - Required when creating a new Service
      type: str
    is_service_https:
      description: Flag whether or not the service cluster uses https
      default: false
      type: bool
    is_internal_route:
      description:
        - Flag whether or not the service is an internal route.
        - Internal routes are only accessible to other services.
      type: bool
    enable_gateway_auth:
      description: If false, the AAP gateway will not insert a gateway token into the proxied request
      type: bool
      default: true
    enable_mtls:
      description: If true, this route will require mutual TLS authentication, and the client needs to provide a certificate. Default is false.
      type: bool
      default: false
    service_path:
      description:
      - URL path on the AAP Service cluster to route traffic to
      - Required when creating a new Service
      type: str
    service_port:
      description:
      - Port on the service cluster to route traffic to
      - Required when creating a new Service
      type: int
    node_tags:
      description:
      - Comma separated string
      - Selects which (tagged) nodes receive traffic from this route
      type: str
    order:
      description:
      - The order to apply the routes in lower numbers are first. Items with the same value have no guaranteed order
      - Defaults to 50 when created
      type: int

extends_documentation_fragment:
- ansible.platform.state
- ansible.platform.auth
"""

EXAMPLES = """
- name: Create service
  ansible.platform.service:
    name: Hub API
    description: Proxy to the Automation Hub
    api_slug: "hub"
    http_port: "Port 8080"
    service_cluster: "Automation Hub"
    is_service_https: true
    service_path: '/api/v1/'
    service_port: 8000
    order: 100

- name: Update service
  ansible.platform.service:
    name: Hub API
    service_path: '/api/v2/'

- name: Check service
  ansible.platform.service:
    name: Gateway API
    state: exists

- name: Delete service
  ansible.platform.service:
    name: Gateway API
    state: absent
...
"""

from ..module_utils.aap_module import AAPModule  # noqa
from ..module_utils.aap_service import AAPService  # noqa


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(type="str"),
        description=dict(type="str"),
        api_slug=dict(type="str"),
        http_port=dict(type="str"),
        service_cluster=dict(type="str"),
        is_service_https=dict(type="bool", default=False),
        is_internal_route=dict(type="bool"),
        enable_gateway_auth=dict(type="bool", default=True),
        enable_mtls=dict(type="bool", default=False),
        service_path=dict(type="str"),
        service_port=dict(type="int"),
        node_tags=dict(type="str"),
        order=dict(type="int"),
        state=dict(
            choices=["present", "absent", "exists", "enforced"], default="present"
        ),
    )

    module = AAPModule(argument_spec=argument_spec, supports_check_mode=True)

    # Validate that enable_mtls and enable_gateway_auth cannot both be true
    enable_mtls = module.params["enable_mtls"]
    enable_gateway_auth = module.params["enable_gateway_auth"]

    if enable_mtls and enable_gateway_auth:
        module.fail_json(
            msg="Mutual TLS can only be enabled when gateway auth is disabled"
        )

    AAPService(module).manage()


if __name__ == "__main__":
    main()
