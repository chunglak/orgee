from __future__ import annotations  # PEP 585

import string

TAG_CHARS = string.ascii_letters + string.digits + "_" + "@"


def conv_org_tag(tag: str) -> str:
    def fmt_c(c: str) -> str:
        return c if c in TAG_CHARS else "_"

    return "".join(map(fmt_c, list(tag.lower())))
