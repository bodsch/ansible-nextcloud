#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2020-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, print_function
import os
import re
import json
import pwd
import grp

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}


class NextcloudApps(object):
    """
    """
    module = None

    def __init__(self, module):
        """
        """
        self.module = module

        self.apps = module.params.get("apps")
        self.working_dir = module.params.get("working_dir")
        self.owner = module.params.get("owner")

        self.occ_base_args = [
            "sudo",
            "--preserve-env",
            "--user",
            self.owner,
            "php",
            "occ"
        ]

    def run(self):
        """
        """
        self._occ = os.path.join(self.working_dir, 'occ')

        if not os.path.exists(self._occ):
            return dict(
                failed = True,
                changed = False,
                msg = "missing occ"
            )

        os.chdir(self.working_dir)

        rc, installed, out, err = self.occ_check(check_installed=True)

        # self.module.log(msg=f" rc : '{rc}'")
        # self.module.log(msg=f" out: '{out.strip()}'")
        # self.module.log(msg=f" err: '{err.strip()}'")

        if not installed and rc == 1:
            return dict(
                failed=False,
                changed=False,
                msg=out
            )

        self.existing_apps = self.occ_list_apps()
        self.enabled_apps = [x for x, _ in self.existing_apps.get("enabled", {}).items()]
        self.disabled_apps = [x for x, _ in self.existing_apps.get("disabled", {}).items()]

        self.module.log(f"existing_apps : {self.existing_apps}")
        self.module.log(f"enabled apps  : {self.enabled_apps}")
        self.module.log(f"disabled apps : {self.disabled_apps}")

        result_state = []

        if self.apps:
            for app in self.apps:
                """
                """
                # self.module.log(f" - {user}")

                app_state = app.get("state", "present")
                app_name = app.get("name", None)
                app_settings = app.get("settings", [])
                groups = []

                if app_name:
                    res = {}

                    _, _, _installed = self.occ_path_app(app_name=app_name)

                    self.module.log(f" - {app_name} installed: {_installed}")

                    if app_state in ["present", "enabled"]:

                        if not installed:
                            install_app = self.occ_install_app(app_name=app_name)
                            self.module.log(f" - {install_app}")
                        else:
                            res[app_name] = dict(
                                changed=False,
                                msg="The app has already been installed."
                            )

                        if app_state == "enabled" and (app_name in self.disabled_apps or not installed):
                            enabled_app = self.occ_enable_app(app_name=app_name, groups=groups)
                            self.module.log(f" - {enabled_app}")

                        _settings_failed, _settings_changed, _settings_msg = self.occ_app_settings(app_name=app_name, app_settings=app_settings)

                        res[app_name] = dict()

                    elif app_state in ["absent", "disabled"]:

                        if app_state == "disabled" and (app_name in self.enabled_apps or installed):
                            res[app_name] = self.occ_disable_app(app_name=app_name)

                        if app_state == "absent":
                            if app_name in self.existing_apps:
                                res[app_name] = self.occ_remove_app(name=app_name)
                            else:
                                res[app_name] = dict(
                                    changed=False,
                                    msg="The app does not exist (anymore)."
                                )

                    result_state.append(res)

                else:
                    pass

        _state, _changed, _failed, state, changed, failed = results(self.module, result_state)

        # self.module.log(msg=f" - state   {_state} '{state}'")
        # self.module.log(msg=f" - changed {_changed} '{changed}'")
        # self.module.log(msg=f" - failed  {_failed} '{failed}'")

        result = dict(
            changed = _changed,
            failed = False,
            state = result_state
        )

        # self.module.log(msg=f" = {result}")

        return result

    def occ_check(self, check_installed=False):
        """
            sudo -u www-data php occ check
        """
        # self.module.log(msg=f"occ_check({check_installed})")

        args = []
        args += self.occ_base_args

        args.append("check")
        args.append("--no-ansi")
        args.append("--output")
        args.append("json")

        # self.module.log(msg=f" args: '{args}'")

        rc, out, err = self.__exec(args, check_rc=False)

        """
            not installed: "Nextcloud is not installed - only a limited number of commands are available"
            installed: ''
        """
        # self.module.log(msg=f" rc : '{rc}'")
        # self.module.log(msg=f" out: '{out.strip()}'")
        # self.module.log(msg=f" err: '{err.strip()}'")

        if not check_installed:
            return rc, out, err

        installed = False

        if rc == 0:
            pattern = re.compile(r"Nextcloud is not installed.*", re.MULTILINE)
            # installed_out = re.search(pattern_1, out)
            is_installed = re.search(pattern, err)

            # self.module.log(msg=f" out: '{installed_out}'")
            # self.module.log(msg=f" err: '{is_installed}' {type(is_installed)}")

            if is_installed:
                installed = False
            else:
                installed = True

        else:
            err = out.strip()

            pattern = re.compile(r"An unhandled exception has been thrown:\n(?P<exception>.*)\n.*", re.MULTILINE)
            exception = re.search(pattern, err)

            if exception:
                err = exception.user("exception")

        # self.module.log(msg=f"{rc} '{installed}' '{out}' '{err}'")

        return (rc, installed, out, err)

    def occ_install_app(self, app_name):
        """
            sudo -u www-data php occ
                user:add
                --no-ansi            if len(groups) > 0:
                _groups = self.occ_add_app_to_groups(app_name=name, groups=groups)
                --display-name="foo"
                "foo"
        """
        self.module.log(msg=f"occ_install_app({app_name})")
        _failed = True
        _changed = False
        _msg = ""

        args = []
        args += self.occ_base_args

        args.append("app:install")
        args.append("--no-ansi")
        args.append(app_name)

        rc, out, err = self.__exec(args, check_rc=False)

        if rc == 0:
            _msg = "App was successfully created."
            _failed = False
            _changed = True
        else:
            _failed = True
            _changed = False
            _msg = out.strip()

        return dict(
            failed=_failed,
            changed=_changed,
            msg=_msg
        )

    def occ_remove_app(self, app_name):
        """
            sudo -u www-data php occ
                user:delete
                --no-ansi
                "foo"
        """
        # self.module.log(msg=f"occ_remove_app({app_name})")
        _failed = True
        _changed = False
        _msg = ""

        args = []
        args += self.occ_base_args

        args.append("app:remove")
        args.append("--no-ansi")
        args.append(app_name)

        self.module.log(msg=f" args: '{args}'")

        rc, out, err = self.__exec(args, check_rc=False)

        # self.module.log(msg=f" rc : '{rc}'")
        # self.module.log(msg=f" out: {type(out)} - '{out.strip()}'")
        # self.module.log(msg=f" err: {type(err.strip())} - '{err.strip()}'")

        if rc == 0:
            _msg = "App was successfully removed."
            _failed = False
            _changed = True
        else:
            _failed = True
            _changed = False
            _msg = out.strip()

        return dict(
            failed=_failed,
            changed=_changed,
            msg=_msg
        )

    def occ_path_app(self, app_name):
        """
            sudo -u www-data php occ
                user:add
                --no-ansi            if len(groups) > 0:
                _groups = self.occ_add_app_to_groups(app_name=name, groups=groups)
                --display-name="foo"
                "foo"
        """
        self.module.log(msg=f"occ_path_app({app_name})")
        _failed = True
        _changed = False

        args = []
        args += self.occ_base_args

        args.append("app:getpath")
        args.append("--no-ansi")
        args.append(app_name)

        rc, out, err = self.__exec(args, check_rc=False)

        if rc == 0:
            # self.module.log(msg=f"  {out})")
            _installed = True
            _failed = False
            _changed = True
        else:
            _installed = False
            _failed = True
            _changed = False

        return (_failed, _changed, _installed)

    def occ_enable_app(self, app_name, groups=[]):
        """
            sudo -u www-data php occ
                user:add
                --no-ansi            if len(groups) > 0:
                _groups = self.occ_add_app_to_groups(app_name=name, groups=groups)
                --display-name="foo"
                "foo"
        """
        self.module.log(msg=f"occ_install_app({app_name}, {groups})")
        _failed = True
        _changed = False
        _msg = ""

        args = []
        args += self.occ_base_args

        args.append("app:enable")
        args.append("--no-ansi")
        args.append(app_name)

        if len(groups):
            for g in groups:
                args.append("--groups")
                args.append(g)

        rc, out, err = self.__exec(args, check_rc=False)

        if rc == 0:
            _msg = "App was successfully enabled."
            _failed = False
            _changed = True
        else:
            _failed = True
            _changed = False
            _msg = out.strip()

        return dict(
            failed=_failed,
            changed=_changed,
            msg=_msg
        )

    def occ_disable_app(self, app_name):
        """
            sudo -u www-data php occ
                user:add
                --no-ansi            if len(groups) > 0:
                _groups = self.occ_add_app_to_groups(app_name=name, groups=groups)
                --display-name="foo"
                "foo"
        """
        self.module.log(msg=f"occ_disable_app({app_name})")
        _failed = True
        _changed = False
        _msg = ""

        args = []
        args += self.occ_base_args

        args.append("app:disable")
        args.append("--no-ansi")
        args.append(app_name)

        rc, out, err = self.__exec(args, check_rc=False)

        if rc == 0:
            _msg = "App was successfully disabled."
            _failed = False
            _changed = True
        else:
            _failed = True
            _changed = False
            _msg = out.strip()

        return dict(
            failed=_failed,
            changed=_changed,
            msg=_msg
        )

    def occ_update_app(self, app_name):
        pass

    def occ_app_settings(self, app_name, app_settings):
        """
        """
        failed = False
        changed = False
        msg = "not to do."

        return (failed, changed, msg)

    def occ_list_apps(self):
        """
        """
        app_names = []
        args = []
        args += self.occ_base_args

        args.append("app:list")
        args.append("--no-ansi")
        args.append("--output")
        args.append("json")

        rc, out, err = self.__exec(args, check_rc=False)

        if rc == 0:
            out = json.loads(out)

            # self.module.log(f"existing_apps : {out}")

            app_names = out  # [x for x, _ in out.items()]

        return app_names

    def occ_app_info(self, app_name):
        """
            sudo -u www-data php occ
                user:info
                --no-ansi
                --output json
                bob
        """
        # self.module.log(msg=f"occ_app_info({app_name})")

        args = []
        args += self.occ_base_args

        args.append("app:info")
        args.append("--no-ansi")
        args.append("--output")
        args.append("json")
        args.append(app_name)

        rc, out, err = self.__exec(args, check_rc=False)

        if rc == 0:
            out = json.loads(out)
            out.update({"state": "present"})
        else:
            out = dict(
                app_id=app_name,
                state="absent",
                msg=out.strip()
            )

        return out

    def __file_state(self, file_name):
        """
        """
        current_owner = None
        current_app = None
        current_mode = None

        if os.path.exists(file_name):
            _state = os.stat(file_name)
            try:
                current_owner = pwd.getpwuid(_state.st_uid).pw_uid
            except KeyError:
                pass

            try:
                current_app = grp.getgrgid(_state.st_gid).gr_gid
            except KeyError:
                pass

            try:
                current_mode = oct(_state.st_mode)[-4:]
            except KeyError:
                pass

        return current_owner, current_app, current_mode

    def __exec(self, commands, check_rc=True):
        """
        """
        rc, out, err = self.module.run_command(
            commands,
            cwd=self.working_dir,
            check_rc=check_rc)

        # self.module.log(msg=f"  rc : '{rc}'")
        if rc != 0:
            self.module.log(msg=f"cmd: '{commands}'")
            self.module.log(msg=f"  rc : '{rc}'")
            self.module.log(msg=f"  out: '{out}'")
            self.module.log(msg=f"  err: '{err}'")
            for line in err.splitlines():
                self.module.log(msg=f"   {line}")

        return rc, out, err


def main():
    """
    """
    specs = dict(
        apps=dict(
            required=False,
            type=list,
            default=[]
        ),
        working_dir=dict(
            required=True,
            type=str
        ),
        owner = dict(
            required=False,
            type=str,
            default = "www-data"
        ),
    )

    module = AnsibleModule(
        argument_spec=specs,
        supports_check_mode=False,
    )

    kc = NextcloudApps(module)
    result = kc.run()

    module.log(msg=f"= result : '{result}'")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()


"""
sudo --user www-data php occ app

      app:disable
      app:enable
      app:getpath
      app:install
      app:list
      app:remove
      app:update

      config:app:delete
      config:app:get
      config:app:set
      files:scan-app-data
      integrity:check-app
      integrity:sign-app
      user:add-app-password

"""
