import re


def parse_improvement_percent(text: str) -> float | None:
    """Parses improvement percentage from standard string format."""
    if "N/A" in text:
        return None
    match = re.search(r"(\d+\.\d+)%", text)
    return float(match.group(1)) if match else None


def route_to_string(cities: list[str]) -> str:
    """Converts list of cities to a formatted directional string."""
    return " → ".join(cities)
