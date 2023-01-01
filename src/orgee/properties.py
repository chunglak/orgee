from __future__ import annotations  # PEP 585

import shlex
from dataclasses import dataclass, field


@dataclass
class OrgProperties:
    properties: list[OrgProperty] = field(default_factory=list)

    @staticmethod
    def from_raw(tus: list[tuple[str, str]]) -> OrgProperties:
        return OrgProperties(
            properties=[OrgProperty.from_raw(tu) for tu in tus]
        )

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

    def dump(self, consolidate_keys: bool = True) -> list[tuple[str, str]]:
        ops = self.consolidate_keys() if consolidate_keys else self
        return [op.dump() for op in ops.properties]

    def dumps(
        self, consolidate_keys: bool = True, create_drawer: bool = True
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


@dataclass
class OrgProperty:
    key: str
    values: list[bool | float | int | str] = field(default_factory=list)

    @staticmethod
    def from_raw(tu: tuple[str, str]) -> OrgProperty:
        key, strval = tu
        return OrgProperty(key=key, values=parse_property(strval))

    def dump(self) -> tuple[str, str]:
        return (self.key, dump_property(self.values))

    def dumps(self) -> str:
        k, v = self.dump()
        return f":{k}: {v}"


def parse_property(s: str) -> list[bool | float | int | str]:
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

    # s = s.replace('\\"', '"')
    # Escape single quotes
    # shlex thinks single quotes should go in pairs...
    s = s.replace("'", "\\'")
    fs = shlex.split(s)
    # Unescape single quotes
    fs = [f.replace("\\'", "'") for f in fs]
    return list(map(process, fs))


def dump_property(v: list[bool | float | int | str]) -> str:
    def quote(s) -> str:
        if s is True:
            return "t"
        elif s is False:
            return "nil"
        elif not s:
            return ""
        elif isinstance(s, str):
            # Escape double quotes
            s = s.replace('"', '\\"')
            # Surround string with spaces with double quotes
            return f'"{s}"' if " " in s else s
        else:
            return str(s)

    if isinstance(v, (list, tuple)):
        return " ".join(map(quote, v))
    else:
        return quote(v)
