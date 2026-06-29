import random


def predict_fuel(distance, traffic):
    """
    Simple AI model (simulated)
    distance → km
    traffic → 1 to 10
    """
    fuel = distance * 0.2 + traffic * 0.5 + random.uniform(0, 1)
    return round(fuel, 2)


def eco_score(distance, fuel):
    """
    Higher score = better route
    """
    score = 100 - (distance * 2 + fuel * 5)
    return round(score, 2)


def choose_best_route(routes):
    best = None
    best_score = -999

    for route in routes:
        fuel = predict_fuel(route["distance"], route["traffic"])
        score = eco_score(route["distance"], fuel)

        route["fuel"] = fuel
        route["eco_score"] = score

        if score > best_score:
            best_score = score
            best = route

    return best, routes
