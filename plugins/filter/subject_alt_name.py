# Copyright: (c) 2022, Ansible Automation Platform
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

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
