#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2024, Bryan Havenstein <@bhavenst>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: service_type
author: Bryan Havenstein (@bhavenst)
short_description: Configure a gateway service type.
description:
    - Configure an automation platform gateway service type.
options:
    name:
      required: true
      type: str
      description: The name of the AAP Service Type, must be unique
    new_name:
      type: str
      description: Setting this option will change the existing name (looked up via the name field)
    ping_url:
      type: str
      description: Ping/status API path for service type
    login_path:
      type: str
      description: API path to login for the service type
    logout_path:
      type: str
      description: API path to logout for the service type
    service_index_path:
      type: str
      description: API path to resource service index endpoint for the service type

extends_documentation_fragment:
- ansible.platform.state
- ansible.platform.auth
"""


EXAMPLES = """
- name: Add service type
  ansible.platform.service_type:
    name: eda
    ping_url: /api/eda/v1/status/
    login_path: /v1/auth/session/login/
    logout_path: /v1/auth/session/logout/
    service_index_path: /service-index/
    state: present

- name: Delete service cluster
  ansible.platform.service_type:
    name: eda
    state: absent

- name: Check if service type exists
  ansible.platform.service_type:
    name: eda
    state: exists
...
"""

from ..module_utils.aap_module import AAPModule  # noqa
from ..module_utils.aap_service_type import AAPServiceType  # noqa


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True, type='str'),
        new_name=dict(type='str'),
        ping_url=dict(type="str"),
        login_path=dict(type="str"),
        logout_path=dict(type="str"),
        service_index_path=dict(type="str"),
        state=dict(choices=["present", "absent", "exists", "enforced"], default="present"),
    )

    # Create a module with spec
    module = AAPModule(argument_spec=argument_spec, supports_check_mode=True)

    # Manage objects through API
    AAPServiceType(module).manage()


if __name__ == "__main__":
    main()
