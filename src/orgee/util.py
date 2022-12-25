from __future__ import annotations

import itertools
import os.path
import re
import shlex


def parse_link(s: str) -> tuple[str, str] | None:
    if m := re.match(r"\[\[(.+)\]\[(.+)\]\]", s.strip()):
        url, title = m.groups()
        return (title, url)
    elif m := re.match(r"\[\[(.+)\]\]", s.strip()):
        url = m.groups()[0]
        return (url, url)
    else:
        return None


def make_link(title: str, url: str) -> str:
    return f"[[{escape_url(url)}][{title}]]"


def is_org_file(fn: str) -> bool:
    return fn.lower().endswith(".org") and not os.path.basename(fn).startswith(
        ".#"
    )


def extract_url(s: str) -> str:
    m = re.match(r"\[\[(.+)\]\[.+\]\]", s.strip())
    return m.groups()[0] if m else ""


def escape_url(url: str) -> str:
    return url.replace("\\", "\\\\").replace("[", r"\[").replace("]", r"\]")


def unescape_url(eurl: str) -> str:
    return eurl.replace(r"\[", "[").replace(r"\]", "]").replace("\\\\", "\\")


def prop_by_key(
    key: str, props: list[tuple[str, str]], parse=True, case_insensitive=True
) -> list[str]:
    vs: list = []
    for k, v in props:
        if comp(k, key, case_insensitive=case_insensitive):
            if isinstance(v, (list, tuple)):
                vs.extend(v)
            else:
                vs.append(v)
    if parse:
        return list(itertools.chain.from_iterable(map(parse_property, vs)))
    else:
        return vs


def first_prop_by_key(
    key: str, props: list[tuple[str, str]], parse=True, case_insensitive=True
) -> str | None:
    ps = prop_by_key(key, props, parse=parse, case_insensitive=case_insensitive)
    return ps[0] if ps else None


def replace_prop(
    key: str, props: list[tuple[str, str]], value=None, case_insensitive=True
) -> tuple[list, list[tuple[str, str]]]:
    ps = prop_by_key(key=key, props=props, case_insensitive=case_insensitive)
    nps = [
        (k, v)
        for k, v in props
        if not comp(k, key, case_insensitive=case_insensitive)
    ]
    if value is not None:
        nps.append((key, dump_property(value)))
    return (ps, nps)


def comp(k1: str, k2: str, case_insensitive=True):
    return k1 == k2 or (case_insensitive and k1.lower() == k2.lower())


def parse_property(s: str) -> tuple:
    def process(s):
        if s == "t":
            return True
        elif s == "nil":
            return False
        else:
            return s

    # s = s.replace('\\"', '"')
    # Escape single quotes
    # shlex thinks single quotes should go in pairs...
    s = s.replace("'", "\\'")
    fs = shlex.split(s)
    # Unescape single quotes
    fs = [f.replace("\\'", "'") for f in fs]
    return tuple(map(process, fs))  # type:ignore


def dump_property(v) -> str:
    def quote(s) -> str:
        if s is True:
            return "t"
        elif s is False:
            return "nil"
        elif not s:
            return ""
        elif isinstance(s, str):
            s = s.replace('"', '\\"')
            return f'"{s}"' if " " in s else s
        else:
            return s

    if isinstance(v, (list, tuple)):
        return " ".join(map(quote, v))
    else:
        return quote(v)


def clean_text(s: str) -> str:
    """
    Return raw text
    """
    # TODO: remove emphasis marks
    s = s.strip()
    # Recursively remove the links urls from heading
    m = re.match(r"(.*)\[\[.+?\]\[(.+?)\]\](.*)", s)
    if m:
        return clean_text("".join(m.groups()))
    # Remove cookie counter
    m = re.match(r"(.+) \[\d*/\d*\]$", s)
    return m.groups()[0] if m else s


def sanitize_for_org(txt: str) -> str:
    def clean(l):
        if l.startswith("*"):
            return " ".join(l.split(" ")[1:])
        else:
            return l

    return "\n".join(map(clean, txt.split("\n")))
