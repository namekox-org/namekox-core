#! -*- coding: utf-8 -*-

# author: forcemain@163.com


from __future__ import print_function


import os
import sys
import yaml
import argparse


from functools import partial
from pkg_resources import get_distribution
from namekox_core.constants import COMMAND_CONFIG_KEY
from namekox_core.core.loaders import import_dotpath_class
from namekox_core.core.parsers.base import recursive_replace_env_var
from namekox_core.core.parsers.patterns import ENV_VAR_MATCHER, IMPLICIT_ENV_VAR_MATCHER
from namekox_core.constants import LOGGING_CONFIG_KEY, DEFAULT_LOGGING_LEVEL, DEFAULT_LOGGING_FORMAT


from .subcmd.base import BaseCommand


DEFAULT_COMMANDS = [
    'namekox_core.cli.subcmd.run:Run',
    'namekox_core.cli.subcmd.shell:Shell',
    'namekox_core.cli.subcmd.config:Config',
]


def env_var_constructor(loader, node, raw=False):
    raw_value = loader.construct_scalar(node)
    value = ENV_VAR_MATCHER.sub(recursive_replace_env_var, raw_value)
    return value if raw else yaml.safe_load(value)


def setup_yaml_parser():
    yaml.add_implicit_resolver(
        '!env_var', IMPLICIT_ENV_VAR_MATCHER, Loader=yaml.UnsafeLoader
    )
    yaml.add_constructor(
        '!env_var', env_var_constructor, Loader=yaml.UnsafeLoader
    )
    yaml.add_constructor(
        '!raw_env_var', partial(env_var_constructor, raw=True), yaml.UnsafeLoader
    )


def get_cfg_from_yaml(f):
    if not os.path.exists(f) or not os.path.isfile(f):
        data = {}
    else:
        fobj = open(f, 'rb')
        data = yaml.unsafe_load(fobj) or {}
        fobj.close()
    return data


def get_cmd_from_conf(c):
    cmds = set(c.get(COMMAND_CONFIG_KEY, []))
    cmds.update(DEFAULT_COMMANDS)
    return [import_dotpath_class(cmd) for cmd in cmds]


def setup_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version',
                        version=get_distribution('namekox_core').version)
    config_file = os.path.join('.', 'config.yaml')
    config_data = get_cfg_from_yaml(config_file)
    sub_command = get_cmd_from_conf(config_data)
    sub_parsers = parser.add_subparsers()
    for err, cmd in sub_command:
        if cmd is None:
            continue
        if err is not None:
            continue
        if not issubclass(cmd, BaseCommand):
            continue
        cmd_parser = sub_parsers.add_parser(
            cmd.name(), help=cmd.__doc__, description=cmd.__doc__)
        cmd_runner = partial(cmd.main, config=config_data)
        cmd_parser.set_defaults(main=cmd_runner)
        cmd.init_parser(cmd_parser, config=config_data)
    return parser


def main():
    setup_yaml_parser()
    if '.' not in sys.path:
        sys.path.insert(0, '.')
    parser = setup_args_parser()
    result = parser.parse_args()
    result.main(result)