#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2024, Martin Slemr <@slemrmartin>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: route
author: Martin Slemr (@slemrmartin)
short_description: Configure a gateway custom (non-api) route.
description:
    - Configure an automation platform gateway additional routes.
    - Their path is outside of the routes that are served from API_PREFIX (/api)
options:
    name:
      required: true
      type: str
      description: The name of the non-api Route, must be unique
    new_name:
      type: str
      description: Setting this option will change the existing name (looked up via the name field)
    description:
      description: The description of the Route
      type: str
    gateway_path:
      description:
      - Path on the AAP gateway to listen to traffic on
      - Required when creating a new route
      type: str
    http_port:
      description:
      - Name or ID referencing the Http Port
      - Required when creating a new route
      type: str
    service_cluster:
      description:
      - Name or ID referencing the Service Cluster
      - Required when creating a new route
      type: str
    is_service_https:
      description: Flag whether or not the service cluster uses https
      default: false
      type: bool
    enable_gateway_auth:
      description: If false, the AAP gateway will not insert a gateway token into the proxied request
      type: bool
      default: true
    enable_mtls:
      description: If false, the AAP gateway will not require mutual TLS authentication
      type: bool
      default: false
    is_internal_route:
      description:
        - Flag whether or not the route is an internal route.
        - Internal routes are only accessible to other services.
      type: bool
    service_path:
      description:
      - URL path on the AAP Service cluster to route traffic to
      - Required when creating a new route
      type: str
    service_port:
      description:
      - Port on the service cluster to route traffic to
      - Required when creating a new route
      type: int
    node_tags:
      description:
      - Comma separated string
      - Selects which (tagged) nodes receive traffic from this route
      type: str

extends_documentation_fragment:
- ansible.platform.state
- ansible.platform.auth
"""

EXAMPLES = """
- name: Create route
  ansible.platform.route:
    name: Controller API
    description: Proxy to the Controller
    http_port: 1                                # ID of http_port
    gateway_path: '/config/controller/'
    service_cluster: "Automation Controller"
    is_service_https: true
    service_path: '/config/v1/'
    service_port: 3000

- name: Create route with mTLS enabled
  ansible.platform.route:
    name: EDA Event Stream
    description: EDA Event Stream with mTLS
    http_port: 1
    gateway_path: '/eda/events/'
    service_cluster: "Event Driven Automation"
    is_service_https: true
    enable_gateway_auth: false                  # Required for mTLS
    enable_mtls: true                           # Enable mutual TLS
    service_path: '/events/'
    service_port: 8080

- name: Update route
  ansible.platform.route:
    name: 1                                     # ID of route
    gateway_path: '/controller-config/'

- name: Check route
  ansible.platform.route:
    name: Controller API
    state: exists

- name: Delete route
  ansible.platform.route:
    name: Controller API
    state: absent
...
"""

from ..module_utils.aap_module import AAPModule
from ..module_utils.aap_route import AAPRoute


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(type="str"),
        description=dict(type="str"),
        gateway_path=dict(type="str"),
        http_port=dict(type="str"),
        service_cluster=dict(type="str"),
        is_service_https=dict(type="bool", default=False),
        is_internal_route=dict(type="bool"),
        enable_gateway_auth=dict(type="bool", default=True),
        enable_mtls=dict(type="bool", default=False),
        service_path=dict(type="str"),
        service_port=dict(type="int"),
        node_tags=dict(type="str"),
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

    AAPRoute(module).manage()


if __name__ == "__main__":
    main()
