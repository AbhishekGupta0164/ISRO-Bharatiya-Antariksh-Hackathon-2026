import uvicorn

from apps.backend.main import app


def main():
    """Server entry point as required by the OpenEnv validator."""
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
