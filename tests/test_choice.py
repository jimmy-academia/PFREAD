import sys, os
sys.path.insert(0, os.path.abspath('.'))

from pfread.parser.choice_expander import expand_choices


def test_expand_choices():
    source = "A \\choice{B}{C} D"
    variants = expand_choices(source)
    assert "A B D" in variants
    assert "A C D" in variants
    assert len(variants) == 2
