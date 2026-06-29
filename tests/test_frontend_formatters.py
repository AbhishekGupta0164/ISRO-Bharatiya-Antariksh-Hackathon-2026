from apps.frontend.utils.formatters import parse_improvement_percent, route_to_string


def test_parse_improvement_percent():
    assert parse_improvement_percent("12.50% less pollution") == 12.5
    assert parse_improvement_percent("N/A") is None


def test_route_to_string():
    assert route_to_string(["A", "B", "F"]) == "A → B → F"
