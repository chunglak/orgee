from __future__ import annotations  # PEP 585

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterator  # pylint:disable=unused-import

from .util import (
    prop_by_key,
    first_prop_by_key,
    replace_prop,
    clean_text,
    extract_url,
)

NOT_FOUND = -1


@dataclass
class RootMeta:
    # List of custom todos for the file
    ptodos: tuple[list[str], list[str]] | None = None
    # These are the files-wide properties (#+PROPERTY:)
    # Not the ones inside the properties drawer
    properties: list[str] = field(default_factory=list)
    # Other #+-type of file-wide settings
    other_meta: list[tuple[str, str]] = field(default_factory=list)

    @property
    def todos(self) -> tuple[list[str], list[str]]:
        return self.ptodos if self.ptodos else (["TODO"], ["DONE"])

    def todo_type(self, kw: str) -> int:
        todos, dones = self.todos
        if kw in todos:
            return 1
        elif kw in dones:
            return -1
        else:
            return 0

    def other_meta_by_key(
        self, key: str, parse=True, case_insensitive=True
    ) -> list:
        return prop_by_key(
            key=key,
            props=self.other_meta,
            parse=parse,
            case_insensitive=case_insensitive,
        )

    def first_other_meta_by_key(
        self, key: str, parse=True, case_insensitive=True
    ) -> str | None:
        return first_prop_by_key(
            key=key,
            props=self.other_meta,
            parse=parse,
            case_insensitive=case_insensitive,
        )


class OrgNode:
    """
    If a node is a root nod (file node) then
    it has no parent, but it has a root_meta
    """

    def __init__(
        self,
        title: str | None = None,
        todo: str | None = None,
        tags: set[str] | None = None,
        counter_cookie: tuple[int, int] | None = None,
        body: list[str] | None = None,
        is_root=False,
        parent: OrgNode | None = None,
    ):
        self.root_meta: RootMeta | None = RootMeta() if is_root else None
        self.parent: OrgNode | None = parent
        # A node cannot both be a root node and have a parent
        assert not (self.root_meta and self.parent)
        # This lineno only works at import time
        # When the nodes are changed it's not valid anymore
        self.lineno: int = 1
        self.properties: list[tuple[str, str]] = []
        self.children: list[OrgNode] = []
        self.todo: str | None = todo
        self.level: int | None = None
        self.title: str = title if title else ""
        self.body: list[str] = body if body else []
        self.tags: set[str] = tags if tags else set()
        self.counter_cookie: tuple[int, int] | None = counter_cookie
        self.find_child_by_title_index: int = NOT_FOUND

    def all_tags(self) -> set[str]:
        """
        Return both the node's own tags and all the tags inherited from parent(s)
        """
        if self.parent:
            return self.tags | self.parent.all_tags()
        else:
            return self.tags

    def node_hash(self) -> str:
        return hashlib.sha256(self.dumps().encode("utf8")).hexdigest()

    def prop_by_key(self, key: str, parse=True, case_insensitive=True) -> list:
        return prop_by_key(
            key=key,
            props=self.properties,
            parse=parse,
            case_insensitive=case_insensitive,
        )

    def first_prop_by_key(
        self, key: str, parse=True, case_insensitive=True
    ) -> str | None:
        ps = self.prop_by_key(
            key=key, parse=parse, case_insensitive=case_insensitive
        )
        return ps[0] if ps else None

    def replace_prop(self, key, value=None) -> list:
        ps, self.properties = replace_prop(
            key=key, props=self.properties, value=value
        )
        return ps

    def recurse_nodes(self) -> list[OrgNode]:
        """
        Depth-first traversal
        """
        nodes = [self]
        for c in self.children:
            nodes.extend(c.recurse_nodes())
        return nodes

    def olp(self) -> list[str]:
        if self.parent:
            return self.parent.olp() + [self.title]
        else:
            return [self.title]

    def olp_str(self) -> str:
        return " → ".join(self.olp())

    def dump_root(self, fn: str):
        """
        Dump whole tree to file starting from root
        """
        with open(fn, "w", encoding="utf-8") as fh:
            fh.write(self.get_root().dumps())

    def dump(self, fn: str):
        with open(fn, "w", encoding="utf-8") as fh:
            fh.write(self.dumps())

    def dumps(self) -> str:
        ls: list[str] = []
        if rm := self.root_meta:
            if self.properties:
                ls.append(":PROPERTIES:")
                for k, v in self.properties:
                    ls.append(f":{k}: {v}")
                ls.append(":END:")
            if self.title:
                ls.append(f"#+TITLE: {self.title}")
            if tags := sorted(self.tags):
                ls.append(f"#+FILETAGS: {' '.join(tags)}")
            if ptodos := rm.ptodos:
                ls.append(
                    "#+TODO: %s | %s"
                    % (" ".join(ptodos[0]), " ".join(ptodos[1]))
                )
            if ps := rm.properties:
                for p in ps:
                    ls.append(f"#+PROPERTY: {p}")
            if ms := rm.other_meta:
                for k, v in ms:
                    ls.append(f"#+{k.upper()}: {v}")
        else:
            ls.append(self.dump_heading())
            if self.properties:
                ls.append(":PROPERTIES:")
                for k, v in self.properties:
                    ls.append(f":{k}: {v}")
                ls.append(":END:")
        if body := self.body:
            ls.append("\n".join(body))
        for c in self.children:
            ls.append(c.dumps())
        return "\n".join(ls)
        # return ("\n".join(ls)).strip()

    def dump_heading(self) -> str:
        if self.root_meta:
            raise Exception("No heading for root node")
        fs: list = ["*" * self.actual_level()]
        fs.append(self.todo)
        fs.append(self.title)
        if tu := self.counter_cookie:
            # pylint: disable=unsubscriptable-object
            fs.append(f"[{tu[0]}/{tu[1]}]")
        if tags := sorted(self.tags):
            fs.append(f":{':'.join(tags)}:")
        return " ".join([f for f in fs if f])

    def actual_level(self) -> int:
        if self.level is not None:
            return self.level
        elif self.parent:
            return self.parent.actual_level() + 1
        else:
            return 0

    def get_root(self) -> OrgNode:
        if self.parent:
            return self.parent.get_root()
        else:
            return self

    def get_root_meta(self) -> RootMeta | None:
        if self.root_meta:
            return self.root_meta
        elif self.parent:
            return self.parent.get_root_meta()
        else:
            return None

    def is_root(self):
        return self.root_meta is not None

    def align_children(self):
        for c in self.children:
            # c.level = (self.level + 1) if self.level else None
            c.level = None
            c.align_children()

    def add_child(
        self, node: OrgNode, auto_align=True, position=-1, replace=False
    ) -> OrgNode:
        """
        TODO: manage case child is a root node
        """
        if auto_align:
            # node.level = (self.level + 1) if self.level else None
            node.level = None
            node.align_children()
        if node.level and self.level and node.level <= self.level:
            raise Exception(
                f"Child level ({node.level}) >= parent level ({self.level})!"
            )
        if position != -1:
            if replace:
                self.children[position] = node
            else:
                self.children.insert(position, node)
        else:
            self.children.append(node)
        node.parent = self
        node.root_meta = None
        return node

    def find_child_by_title(
        self,
        title: str | None = None,
        url: str | None = None,
        tags: list[str] | None = None,
        startswith=False,
    ) -> OrgNode | None:
        def matching(s: str) -> bool:
            if title:
                cs = clean_text(s)
                if startswith:
                    # print(f"cs={cs}\ntitle={title}")
                    if not cs.startswith(title):
                        return False
                elif cs != title:
                    return False
            if url and extract_url(s) != url:
                return False
            return True

        if title:
            title = clean_text(title)
        for i, child in enumerate(self.children):
            # if clean_text(child.title) == title:
            if matching(child.title):
                if tags and not (set(tags) <= set(child.tags)):
                    continue
                self.find_child_by_title_index = i
                return child
        self.find_child_by_title_index = NOT_FOUND
        return None

    def find_olp(
        self, olp: list[str], tags: list[str] | None = None
    ) -> OrgNode | None:
        """
        TODO: Handle case when multiple subtrees (same level) have same name
        """
        if not olp:
            return self
        else:
            n = self.find_child_by_title(title=olp[0], tags=tags)
            if n:
                return n.find_olp(olp[1:])
            else:
                print(f"Failed at {olp[0]}")
                return None

    def clean_title(self) -> str:
        return clean_text(self.title)
