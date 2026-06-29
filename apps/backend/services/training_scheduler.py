import asyncio
import datetime

from apps.backend.core.config import settings
from models.train_model import run_training_pipeline


class TrainingScheduler:
    def __init__(self, interval_seconds: int | None = None):
        self.interval_seconds = interval_seconds or settings.TRAINING_INTERVAL_SECONDS
        self.is_running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self):
        print("Model training scheduler started")
        while self.is_running:
            try:
                success = await asyncio.to_thread(run_training_pipeline)
                status = "completed" if success else "skipped"
                next_run = datetime.datetime.now() + datetime.timedelta(
                    seconds=self.interval_seconds
                )
                print(f"Automated training {status}. Next run at {next_run:%Y-%m-%d %H:%M:%S}.")
            except Exception as exc:  # noqa: BLE001
                print(f"Error during automated training: {exc}")

            await asyncio.sleep(self.interval_seconds)


scheduler = TrainingScheduler()
