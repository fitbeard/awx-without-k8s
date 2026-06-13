#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2024, Martin Slemr <@slemrmartin>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: service_node
author: Martin Slemr (@slemrmartin)
short_description: Configure a gateway service node.
description:
    - Configure an automation platform gateway service node.
options:
    name:
      required: true
      type: str
      description: The name of the Service Node, must be unique
    new_name:
      type: str
      description: Setting this option will change the existing name (looked up via the name field)
    address:
        description:
            - Network address to route traffic for this service to
            - Must be unique
            - Required when creating new Service Node
        type: str
    service_cluster:
        description:
          - Service Cluster containing this node - name or ID
          - Required when creating new Service Node
        type: str
    tags:
      description:
      - Comma separated string
      - All nodes with tags referenced in a route's node_tags will receive traffic from that route
      type: str

extends_documentation_fragment:
- ansible.platform.state
- ansible.platform.auth
"""

EXAMPLES = """
- name: Create service node
  ansible.platform.service_node:
    name: "Controller - Node 1"
    address: 10.0.0.1
    service_cluster: controller

- name: Delete service node
  ansible.platform.service_node:
    name: 3  # ID can be used
    state: absent

- name: Update service node's cluster
  ansible.platform.service_node:
    name: "Controller - Node 1"
    address: 10.0.0.1
    service_cluster: 2 # service cluster's name or ID
...
"""

from ..module_utils.aap_module import AAPModule  # noqa
from ..module_utils.aap_service_node import AAPServiceNode  # noqa


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        new_name=dict(type="str"),
        address=dict(type="str"),
        service_cluster=dict(type="str"),
        tags=dict(type="str"),
        state=dict(choices=["present", "absent", "exists", "enforced"], default="present"),
    )

    # Create a module with spec
    module = AAPModule(argument_spec=argument_spec, supports_check_mode=True)

    # Manage objects through API
    AAPServiceNode(module).manage()


if __name__ == '__main__':
    main()
