"""CLI entrypoint for simulator and trainer."""

from apps.simulator.evaluator import run as run_evaluator
from apps.simulator.trainer import train_fuel_model

if __name__ == "__main__":
    train_fuel_model()
    run_evaluator()
