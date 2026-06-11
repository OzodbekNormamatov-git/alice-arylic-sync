"""Sanity-check Home Assistant blueprint and example YAML files.

Parses every YAML file under blueprints/ and examples/ with a loader that
accepts HA-specific tags (!input) and asserts the minimal blueprint schema.
"""

import glob
import sys

import yaml


class HaLoader(yaml.SafeLoader):
    pass


def _any_tag(loader, suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


yaml.add_multi_constructor("!", _any_tag, HaLoader)

failed = False

for path in sorted(glob.glob("blueprints/**/*.yaml", recursive=True)):
    with open(path, encoding="utf-8") as f:
        data = yaml.load(f, Loader=HaLoader)
    bp = (data or {}).get("blueprint") or {}
    problems = [f"missing blueprint.{key}" for key in ("name", "domain") if not bp.get(key)]
    if bp.get("domain") and bp["domain"] != "automation":
        problems.append(f"unexpected domain {bp['domain']!r}")
    if problems:
        print(f"FAIL {path}: {', '.join(problems)}")
        failed = True
    else:
        print(f"OK   {path}")

for path in sorted(glob.glob("examples/*.yaml")):
    with open(path, encoding="utf-8") as f:
        yaml.load(f, Loader=HaLoader)
    print(f"OK   {path}")

sys.exit(1 if failed else 0)
