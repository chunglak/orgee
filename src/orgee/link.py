from __future__ import annotations  # PEP 585

import re


def extract_url(s: str) -> str | None:
    r = parse_link(s)
    return r[1] if r else None


def parse_link(s: str) -> tuple[str, str] | None:
    """
    Decompose a org link into its uri and description components
    """
    if m := re.match(r"\[\[(.+)\]\[(.+)\]\]", s.strip()):
        uri, title = m.groups()
        return (title, uri)
    elif m := re.match(r"\[\[(.+)\]\]", s.strip()):
        uri = m.groups()[0]
        return ("", uri)
    else:
        return None


def make_link(title: str, uri: str) -> str:
    return f"[[{escape_url(uri)}][{title}]]"


def escape_url(uri: str) -> str:
    return uri.replace("\\", "\\\\").replace("[", r"\[").replace("]", r"\]")
