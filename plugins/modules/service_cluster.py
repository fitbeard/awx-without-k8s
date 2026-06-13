#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2024, Martin Slemr <@slemrmartin>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: service_cluster
author: Martin Slemr (@slemrmartin)
short_description: Configure a gateway service cluster.
description:
    - Configure an automation platform gateway service cluster.
options:
    name:
      required: true
      type: str
      description: The name of the AAP Service, must be unique
    new_name:
      type: str
      description: Setting this option will change the existing name (looked up via the name field)
    service_type:
      type: str
      description:
        - Service Type for this cluster - name or ID
        - Required when creating new Service Cluster
    auth_type:
      type: str
      description:
        - Authentication type for this service cluster
        - Defaults to JWT
      choices: ["JWT", "BASIC", "TOKEN"]
    upstream_hostname:
      type: str
      description:  If set, Server Name Identification(SNI) and host header are set to this value
    dns_discovery_type:
      type: str
      description:
        - DNS discovery type used for this service
        - STRICT_DNS (default) - Use, maintain and load balance among all returned addresses
        - LOGICAL_DNS - Use the first returned address at a time
        - See envoy documentation for further details
      choices: ["STRICT_DNS", "LOGICAL_DNS"]
    dns_lookup_family:
      type: str
      description:
        - DNS address selection control
        - ALL - Use all addresses
        - AUTO - IPv6 preferred
      choices: ["ALL", "V4_ONLY", "V6_ONLY", "V4_PREFERRED", "AUTO"]
    outlier_detection_enabled:
      type: bool
      description: If true, outlier detection will be used to determine if a node is unhealthy and should be ejected from the cluster.
    outlier_detection_consecutive_5xx:
      type: int
      description: Number of consecutive 5xx responses to consider a node unhealthy.
    outlier_detection_interval_seconds:
      type: int
      description: The time interval between ejection analysis sweeps.
    outlier_detection_base_ejection_time_seconds:
      type: int
      description: The base time a node will be ejected for.
    outlier_detection_max_ejection_percent:
      type: int
      description: The maximum percent of nodes that can be ejected from the cluster.
    health_checks_enabled:
      type: bool
      description: If true, health checks will be used to determine if a node is healthy.
    health_check_timeout_seconds:
      type: int
      description: The time to wait for a health check to complete.
    health_check_interval_seconds:
      type: int
      description: The time between health check requests.
    health_check_unhealthy_threshold:
      type: int
      description: The number of consecutive failed health checks before a node is considered unhealthy.
    health_check_healthy_threshold:
      type: int
      description: The number of consecutive successful health checks before a node is considered healthy.
    healthy_panic_threshold:
      type: int
      description: The percentage of failed hosts when the proxy will panic and start routing traffic to all nodes. Set to 0 to disable this.

extends_documentation_fragment:
- ansible.platform.state
- ansible.platform.auth
"""


EXAMPLES = """
- name: Add service cluster
  ansible.platform.service_cluster:
    name: Automation Controller
    service_type: controller
    state: present

- name: Delete service cluster
  ansible.platform.service_cluster:
    name: Automation Controller
    state: absent

- name: Check if cluster exists
  ansible.platform.service_cluster:
    name: Automation Controller
    state: exists
...
"""

from ..module_utils.aap_module import AAPModule  # noqa
from ..module_utils.aap_service_cluster import AAPServiceCluster  # noqa


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True, type='str'),
        new_name=dict(type='str'),
        service_type=dict(type='str'),
        auth_type=dict(choices=['JWT', 'BASIC', 'TOKEN']),
        upstream_hostname=dict(type='str'),
        dns_discovery_type=dict(choices=['STRICT_DNS', 'LOGICAL_DNS']),
        dns_lookup_family=dict(choices=['ALL', 'V4_ONLY', 'V6_ONLY', 'V4_PREFERRED', 'AUTO']),
        state=dict(choices=["present", "absent", "exists", "enforced"], default="present"),
        outlier_detection_enabled=dict(type='bool'),
        outlier_detection_consecutive_5xx=dict(type='int'),
        outlier_detection_interval_seconds=dict(type='int'),
        outlier_detection_base_ejection_time_seconds=dict(type='int'),
        outlier_detection_max_ejection_percent=dict(type='int'),
        health_checks_enabled=dict(type='bool'),
        health_check_timeout_seconds=dict(type='int'),
        health_check_interval_seconds=dict(type='int'),
        health_check_unhealthy_threshold=dict(type='int'),
        health_check_healthy_threshold=dict(type='int'),
        healthy_panic_threshold=dict(type='int'),
    )

    # Create a module with spec
    module = AAPModule(argument_spec=argument_spec, supports_check_mode=True)

    # Manage objects through API
    AAPServiceCluster(module).manage()


if __name__ == "__main__":
    main()
