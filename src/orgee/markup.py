from __future__ import annotations  # PEP 585

import re


def remove_org_markup(s: str) -> str:
    # TODO: remove emphasis marks
    s = s.strip()
    # Recursively remove the links urls from heading
    m = re.match(r"(.*)\[\[.+?\]\[(.+?)\]\](.*)", s)
    if m:
        return remove_org_markup("".join(m.groups()))
    # Remove cookie counter
    m = re.match(r"(.+) \[\d*/\d*\]$", s)
    return m.groups()[0] if m else s


def sanitize_text_for_org(txt: str) -> str:
    """
    In multiline text, escape the lines starting with a star
    """

    def clean(l):
        if l.startswith("*"):
            return " ".join(l.split(" ")[1:])
        else:
            return l

    return "\n".join(map(clean, txt.split("\n")))
