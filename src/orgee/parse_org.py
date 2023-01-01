from __future__ import annotations  # PEP 585

import logging
import re

from .orgnode import OrgNode, RootMeta, TodoType
from .properties import OrgProperty


def parse_org_file(fn: str) -> OrgNode:
    with open(fn, "r", encoding="utf8") as fh:
        return parse_org_document(fh.read())


def parse_org_document(text: str) -> OrgNode:
    return parse_text(text=text.split("\n"), lineno=1, is_root=True)


def parse_text(
    text: list[str], lineno: int, is_root=False, parent: OrgNode | None = None
) -> OrgNode:
    """
    Parse a list of strings into a subtree and its children
    """
    body, children = extract_body_and_children(text, is_root=is_root)
    node = parse_body(body=body, lineno=lineno, is_root=is_root, parent=parent)
    node.children = [
        parse_text(text=child, lineno=lineno + child_lineno, parent=node)
        for child, child_lineno in children
    ]
    return node


def parse_body(
    body: list[str], lineno: int, is_root=False, parent: OrgNode | None = None
) -> OrgNode:
    """
    Parse the body of a subtree (excluding children)
    """
    node = OrgNode(is_root=is_root)
    node.lineno = lineno
    lines = body

    if is_root:
        if parent:
            raise Exception("A root node cannot have a parent!")
    else:
        node.parent = parent
        heading = lines[0]
        lines = lines[1:]
        dic = parse_heading(
            heading=heading,
            root_meta=parent.get_root_meta() if parent else None,
        )
        node.title = dic["title"]
        node.todo = dic.get("todo")
        node.level = dic["level"]
        node.counter_cookie = dic.get("cookie_counter")
        if tags := dic.get("tags"):
            node.tags = set(tags)

    i = 0
    bodyl = []
    in_props = False
    in_env = False
    while i < len(lines):
        line = lines[i]
        lsl = line.rstrip().lower()

        if lsl.startswith("#+begin"):
            in_env = True
        elif in_env and lsl.startswith("#+end"):
            in_env = False

        if lsl == ":properties:":
            if not in_env:
                in_props = True
        elif in_props:
            if lsl == ":end:":
                in_props = False
            else:
                m = re.match(r":([\w:\-\+]+):\s*(.*)\s*", line.lstrip())
                if not m:
                    print(line)
                    raise Exception("Bad property")
                k, v = m.groups()
                node.properties.add_property(OrgProperty.from_raw((k, v)))
        elif is_root and lsl.startswith("#+"):
            assert node.root_meta
            rm = node.root_meta
            m = re.match(r"#\+([\w\-\+]+):\s*(.*)\s*", line.lstrip())
            if not m:
                if lsl.startswith("#+begin_") or lsl.startswith("#+end"):
                    bodyl.append(line)
                    i += 1
                    continue
                print(line)
                raise Exception("Bad file property")
            k, v = m.groups()
            kl = k.lower()
            if kl == "title":
                node.title = v
            elif kl == "filetags":
                # rm.filetags.update([t for t in v.split(" ") if t])
                node.tags.update([t for t in v.split(" ") if t])
            elif kl == "property":
                rm.file_properties.append(v)
            elif kl == "todo":
                if "|" in v:
                    stodos, sdones = v.split("|", maxsplit=1)
                    todos = [t.strip() for t in stodos.split(" ")]
                    dones = [t.strip() for t in sdones.split(" ")]
                else:
                    ts = [t.strip() for t in v.split(" ")]
                    todos = ts[:-1]
                    dones = [ts[-1]]
                rm.todos = ([t for t in todos if t], [t for t in dones if t])
            else:
                node.root_meta.other_meta.append((k, v))
        else:
            bodyl.append(line)

        i += 1
    node.body = bodyl
    return node


def parse_heading(heading: str, root_meta: RootMeta | None = None) -> dict:
    dic: dict = {}
    # Parse stars
    if not heading.startswith("*"):
        logging.error(heading)
        raise Exception("Heading doesn't start with a *!")
    try:
        stars, rest = heading.split(" ", maxsplit=1)
    except ValueError:
        stars, rest = heading, ""
    if not is_stars(stars):
        logging.error(stars)
        raise Exception("Heading doesn't start with stars!")
    dic["level"] = len(stars)
    # Parse todo
    if not root_meta:
        root_meta = RootMeta()
    todosplit = rest.split(" ", maxsplit=1)
    if (
        len(todosplit) > 1
        and root_meta.todo_type(todosplit[0]) is not TodoType.INVALID
    ):
        dic["todo"] = todosplit[0]
        rest = todosplit[1]

    m = re.match(r"(.*?)\s*:([\w@:]+):\s*$", rest)
    if m:
        title, tags = m.groups()
        dic["tags"] = tags.split(":")
    else:
        title = rest
    # Parse cookie counter
    m = re.match(r"(.*?)\s*\[(\d+)/(\d+)\]\s*", rest)
    if m:
        title, c1, c2 = m.groups()
        dic["cookie_counter"] = (int(c1), int(c2))
    dic["title"] = title

    return dic


def extract_body_and_children(
    lines: list[str], is_root=False
) -> tuple[list[str], list[tuple[list[str], int]]]:
    """
    Split a text into a body and a list of children nodes
    """
    body = []
    i = 0

    if not is_root:
        line = lines[i]
        fw = line.split(" ", maxsplit=1)[0]
        if not is_stars(fw):
            print(line)
            raise Exception("Non-root body should start with a heading")
        body.append(line)
        i += 1

    stars = None
    # Search for first heading
    while i < len(lines):
        line = lines[i]
        fw = line.split(" ", maxsplit=1)[0]
        # Stars only without space does not count as heading
        if is_stars(fw) and len(line) > len(fw):
            stars = fw
            break
        body.append(line)
        i += 1
    if not stars:
        return (body, [])
    nodes: list[tuple[list[str], int]] = []
    node = [line]
    lineno = i
    i += 1
    while i < len(lines):
        line = lines[i]
        fw = line.split(" ", maxsplit=1)[0]
        if is_stars(fw) and len(line) > len(fw) and len(fw) <= len(stars):
            stars = fw
            nodes.append((node, lineno))
            lineno = i
            node = [line]
        else:
            node.append(line)
        i += 1
    if node:
        nodes.append((node, lineno))
        lineno = i
    return (body, nodes)


def is_stars(s: str) -> bool:
    return s.startswith("*") and s == "*" * len(s)
