# Copyright: (c) 2025, Ansible Automation Platform
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
name: ipv6_wrap
author: Ansible Automation Platform
short_description: Wrap IPv6 addresses in square brackets
description:
  - Wrap an IPv6 address in square brackets.
  - Return non-IPv6 values unchanged.
positional: _input
options:
  _input:
    description:
      - The address or hostname to inspect.
    type: str
    required: true
"""

EXAMPLES = r"""
- name: Wrap an IPv6 address for URL usage
  ansible.builtin.debug:
    msg: "{{ '2001:db8::1' | fitbeard.awx.ipv6_wrap }}"

- name: Leave hostnames unchanged
  ansible.builtin.debug:
    msg: "{{ 'gateway.demo.io' | fitbeard.awx.ipv6_wrap }}"
"""

RETURN = r"""
_value:
  description:
    - The original value, or the IPv6 address wrapped in square brackets.
  type: str
"""

from ipaddress import IPv6Address


class FilterModule(object):
    """Wrap IPv6 addresses"""

    def ipv6_wrap(self, val):
        try:
            IPv6Address(val)
        except ValueError:
            return val
        return f"[{val}]"

    def filters(self):
        return {"ipv6_wrap": self.ipv6_wrap}
