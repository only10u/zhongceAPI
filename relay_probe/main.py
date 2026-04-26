import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from relay_probe import __version__
from relay_probe.config import Settings
from relay_probe.probe import ProbeResult, result_to_dict, run_probe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("relay_probe")

settings = Settings()
_state: dict[str, Any] = {
    "last": None,
    "last_at": None,
    "version": __version__,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.check_interval_sec > 0:
        t = asyncio.create_task(_background_loop())
        try:
            yield
        finally:
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
    else:
        yield


async def _background_loop() -> None:
    while True:
        res = _run_and_store()
        if res.ok:
            log.info("probe ok latency_ms=%s", res.latency_ms)
        else:
            log.warning("probe fail: %s", res.error or res.http_status)
        await asyncio.sleep(settings.check_interval_sec)


def _run_and_store() -> ProbeResult:
    res = run_probe(settings)
    _state["last"] = result_to_dict(res)
    _state["last_at"] = datetime.now(timezone.utc).isoformat()
    return res


app = FastAPI(title="API Relay Probe", version=__version__, lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/last")
def api_last() -> JSONResponse:
    return JSONResponse(
        content={
            "version": _state.get("version"),
            "last_at": _state.get("last_at"),
            "last": _state.get("last"),
        }
    )


@app.post("/api/check")
def api_check() -> JSONResponse:
    res = _run_and_store()
    payload = result_to_dict(res)
    payload["checked_at"] = _state.get("last_at")
    return JSONResponse(content=payload)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "relay_probe.main:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
    )
