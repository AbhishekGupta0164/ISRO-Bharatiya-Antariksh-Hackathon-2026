from apps.backend.services.route_service import get_route_service


def test_route_service_valid_path():
    result = get_route_service("A", "F")

    assert result["route"][0] == "A"
    assert result["route"][-1] == "F"
    assert result["total_distance"] > 0
    assert "improvement" in result


def test_route_service_invalid_node():
    result = get_route_service("A", "Z")

    assert result["error"] == "Invalid start or end node"
