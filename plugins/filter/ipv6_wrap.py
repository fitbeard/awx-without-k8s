# Copyright: (c) 2025, Ansible Automation Platform
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

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
