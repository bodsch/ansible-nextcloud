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
            'nc_configured_redis': self.configured_redis,
            'nc_configured_cache': self.configured_cache,
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

        _directory_list = [
            "skeleton_directory",
            "template_directory",
            "temp_directory",
            "update_directory",
            "data_directory"
        ]

        dirs = [dirs for keys, dirs in data.items() if keys in _directory_list]
        dirs += [os.path.dirname(dirs) for keys, values in data.items() if keys in ["logging"] for k, dirs in values.items() if k in ["file"]]

        display.v(f"= return : {dirs}")

        return dirs

    def configured_redis(self, data):
        """
        """
        display.v(f"- data : {data}")

        result = [x for x in data if x.get("host", None)]

        return result

    def configured_cache(self, data, cache="redis"):
        """
        """
        display.v(f"- data : {data}")

        if cache == "redis":
            result = [x for x in data if x.get("host", None)]
        if cache == "memcache":
            # memcaches = [x for x in data if x.get("local", None) or x.get("locking", None) or x.get("distributed", None)]
            # if len(memcaches) > 0:
            memcache_servers = data.get("servers", [])
            result = [x for x in memcache_servers if x.get("host", None)]

        display.v(f"- result : {result}")

        return result
