# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Martin Slemr <@slemrmartin>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    # Ansible Galaxy documentation fragment
    DOCUMENTATION = r"""
options:
    state:
      description:
        - Desired state of the resource.
        - Enforced state C(enforced) will default values of any option not provided.
      choices: ["present", "absent", "exists", "enforced"]
      default: "present"
      type: str
"""
