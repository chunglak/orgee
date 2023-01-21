from __future__ import annotations  # PEP 585

import shlex
from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass
class OrgProperties:
    properties: list[OrgProperty] = field(default_factory=list)

    @staticmethod
    def from_raw(tus: list[tuple[str, str]]) -> OrgProperties:
        return OrgProperties(
            properties=[OrgProperty.from_raw(tu) for tu in tus]
        )

    @staticmethod
    def from_rec(rec: list[tuple[str, list]]) -> OrgProperties:
        return OrgProperties(
            properties=[
                OrgProperty(key=key, values=values) for key, values in rec
            ]
        )

    def to_rec(self) -> list[tuple[str, list]]:
        return [(prop.key, prop.values) for prop in self.properties]

    def has_properties(self) -> bool:
        return len(self.properties) > 0

    def add_property(self, prop: OrgProperty):
        self.properties.append(prop)

    def consolidate_keys(self) -> OrgProperties:
        dic: dict = {}
        for prop in self.properties:
            dic.setdefault(prop.key, []).extend(prop.values)
        return OrgProperties(
            properties=[
                OrgProperty(key=key, values=values)
                for key, values in dic.items()
            ]
        )

    def dump(self, consolidate_keys: bool = False) -> list[tuple[str, str]]:
        ops = self.consolidate_keys() if consolidate_keys else self
        return [op.dump() for op in ops.properties]

    def dumps(
        self, consolidate_keys: bool = False, create_drawer: bool = True
    ) -> str:
        ops = self.consolidate_keys() if consolidate_keys else self
        s = "\n".join(op.dumps() for op in ops.properties)
        if create_drawer:
            s = ":PROPERTIES:\n" + s + "\n:END:"
        return s

    def property_by_key(self, key: str) -> list[bool | float | int | str]:
        rez = []
        lkey = key.lower()
        for prop in self.properties:
            if prop.key.lower() == lkey:
                rez.extend(prop.values)
        return rez

    def first_property_by_key(
        self, key: str
    ) -> bool | float | int | str | None:
        ps = self.property_by_key(key=key)
        return ps[0] if ps else None

    def replace_property(
        self,
        key: str,
        new_value: Iterable | bool | float | int | str | None = None,
    ) -> list:
        old_values = self.property_by_key(key)
        lkey = key.lower()
        self.properties = [
            prop for prop in self.properties if prop.key.lower() != lkey
        ]
        if new_value is not None:
            if isinstance(new_value, Iterable) and not isinstance(
                new_value, str
            ):
                new_value = list(new_value)
            else:
                new_value = [new_value]
            self.properties.append(OrgProperty(key=key, values=new_value))
        return old_values


@dataclass
class OrgProperty:
    key: str
    values: list[bool | float | int | str] = field(default_factory=list)

    @staticmethod
    def from_raw(tu: tuple[str, str]) -> OrgProperty:
        key, val = tu
        return OrgProperty(key=key, values=parse_property(key=key, val=val))

    def dump(self) -> tuple[str, str]:
        return (self.key, dump_property(key=self.key, vals=self.values))

    def dumps(self) -> str:
        k, v = self.dump()
        return f":{k}: {v}"


def parse_property(key: str, val: str) -> list[bool | float | int | str]:
    def process(s):
        if s == "t":
            return True
        elif s == "nil":
            return False
        else:
            try:
                return int(s)
            except ValueError:
                try:
                    return float(s)
                except ValueError:
                    return s

    # Do not parse header-args
    if key.lower().startswith("header-args"):
        return [val]
    # s = s.replace('\\"', '"')
    # Escape single quotes
    # shlex thinks single quotes should go in pairs...
    val = val.replace("'", "\\'")
    fs = shlex.split(val)
    # Unescape single quotes
    fs = [f.replace("\\'", "'") for f in fs]
    return list(map(process, fs))


def dump_property(key: str, vals: list[bool | float | int | str]) -> str:
    def quote(s) -> str:
        if s is True:
            return "t"
        elif s is False:
            return "nil"
        elif s is None:
            # return ""
            return "nil"
        elif isinstance(s, str):
            # Escape double quotes
            s = s.replace('"', '\\"')
            # Surround string with spaces with double quotes
            return f'"{s}"' if " " in s else s
        else:
            return str(s)

    # Do not quote header-args
    if key.lower().startswith("header-args"):
        return str(vals[0])
    return " ".join(map(quote, vals))
    # if isinstance(vals, (list, tuple)):
    #     return " ".join(map(quote, vals))
    # else:
    #     return quote(vals)
