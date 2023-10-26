# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """
        Ansible file jinja2 tests
    """

    def filters(self):
        return {
            'directories': self.directories,
            'nc_directories': self.directories,
        }

    def directories(self, data):
        """
          skeleton_directory: ""
          template_directory: ""
          temp_directory: ""
          update_directory: ""
          data_directory: ""
          logging:
            file: ""
            logfile_audit: ""

        """
        dirs = []

        # display.v(f"- data : {data}")

        dirs = [dirs for keys, dirs in data.items() if keys in ["skeleton_directory", "template_directory", "temp_directory", "update_directory", "data_directory"]]
        dirs += [os.path.dirname(dirs) for keys, values in data.items() if keys in ["logging"] for k, dirs in values.items() if k in ["file"]]

        display.v(f"= return : {dirs}")

        return dirs
