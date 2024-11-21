# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
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
            'nc_configured_cache': self.configured_cache,
            'nc_database_driver': self.configured_database,
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

        display.v(f"- data : {data}")

        _directory_list = [
            "skeleton_directory",
            "template_directory",
            "temp_directory",
            "update_directory",
            "data_directory"
        ]

        dirs = [dirs for keys, dirs in data.items() if keys in _directory_list]

        logging_dirs = [
            os.path.dirname(dirs) for keys, values in data.items()
            if keys in ["logging"]
            for k, dirs in values.items()
            if k in ["file"]
        ]

        application_dirs = [
            dirs for keys, values in data.items()
            if keys in ["apps"]
            for k, apps in values.items()
            for app in apps
            for i, dirs in app.items()
            if i in ['path']
        ]

        dirs += logging_dirs
        dirs += application_dirs

        dirs = list(set(dirs))
        # remove empty elements
        dirs = list(filter(None, dirs))

        dirs.sort(reverse=False)

        display.v(f"= return : {dirs}")

        return dirs

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

    def configured_database(self, data, packages):
        """
        """
        display.v(f"configured_database({data}, {packages})")

        database_type = data.get('type')
        package = packages.get(database_type, [])

        display.v(f"- result : {package}")

        return package

    def _validate_upper_and_lower_case(self, password):

        valide = False
        msg = "Password needs to contain at least one lower and one upper case character."

        pattern = re.compile('/^(?=.*[a-z])(?=.*[A-Z]).+$/')
        exception = re.search(pattern, password)

        if exception:
            display.v(f"- exception : {exception}")
        else:
            valide = True
            msg = ""

        return (valide, msg)

    def _validate_special_character(self, password):

        valide = False
        msg = "Password needs to contain at least one special character."

        if password.isalnum():
            valide = True
            msg = ""

        return (valide, msg)

    def _validate_numeric_character(self, password):

        valide = False
        msg = "Password needs to contain at least one numeric character."

        pattern = re.compile('/^(?=.*\d).+$/')
        exception = re.search(pattern, password)

        if exception:
            display.v(f"- exception : {exception}")
        else:
            valide = True
            msg = ""

        return (valide, msg)

    def _validate_length(self, password, length=10):

        valide = False
        msg = f"Password needs to be at least {length} characters long."

        if len(password) >= length:
            valide = True
            msg = ""

        return (valide, msg)
