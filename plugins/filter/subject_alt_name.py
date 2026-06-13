# Copyright: (c) 2022, Ansible Automation Platform
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
name: subject_alt_name
author: Ansible Automation Platform
short_description: Format a value as a certificate subject alternative name
description:
  - Return a value formatted as a certificate subject alternative name.
  - IP addresses are returned with a C(IP:) prefix.
  - Other values are returned with a C(DNS:) prefix.
positional: _input
options:
  _input:
    description:
      - The DNS name or IP address to format.
    type: str
    required: true
"""

EXAMPLES = r"""
- name: Format a DNS subject alternative name
  ansible.builtin.debug:
    msg: "{{ 'gateway.demo.io' | fitbeard.awx.subject_alt_name }}"

- name: Format an IP subject alternative name
  ansible.builtin.debug:
    msg: "{{ '192.0.2.10' | fitbeard.awx.subject_alt_name }}"
"""

RETURN = r"""
_value:
  description:
    - The value formatted as C(DNS:<value>) or C(IP:<value>).
  type: str
"""

from ipaddress import ip_address


class FilterModule(object):
    """Return DNS or IP subject alt name"""

    def subject_alt_name(self, val):
        try:
            ip_address(val)
        except ValueError:
            return "DNS:{}".format(val)
        return "IP:{}".format(val)

    def filters(self):
        return {"subject_alt_name": self.subject_alt_name}
