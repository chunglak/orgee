from orgee.util import parse_property


def test_parse_property1():
    p1 = "prop1"
    p2 = "prop2 foo"
    s = f'{p1} "{p2}"'
    r = parse_property(s)
    assert r == (p1, p2)


def test_parse_property2():
    p1 = "prop1"
    p2 = r"prop2 \"foo\""
    p2p = 'prop2 "foo"'
    s = f'{p1} "{p2}"'
    r = parse_property(s)
    print(r)
    assert r == (p1, p2p)


def test_parse_property3():
    p1 = "prop1"
    p2 = "prop2's"
    s = f'{p1} "{p2}"'
    r = parse_property(s)
    print(r)
    assert r == (p1, p2)


def test_parse_property4():
    s0 = "1967.The Velvet Underground & Nico (45th Anniversary / Super Deluxe Edition)"
    s = r'"\"%s\""' % s0
    r = parse_property(s)
    assert r[0] == f'"{s0}"'
