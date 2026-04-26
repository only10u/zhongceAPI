from relay_probe.model_catalog import match_models
from relay_probe.models import ModelProbeSample
from relay_probe.probe import ProbeResult


def add_model_samples_from_probe(
    session: object, relay_id: int, res: ProbeResult
) -> None:
    if res.ok and res.body_text:
        blob = res.body_text.lower()
        flags = match_models(blob)
    else:
        from relay_probe.model_catalog import TRACKED_MODELS

        flags = {m["slug"]: False for m in TRACKED_MODELS}
    for slug, present in flags.items():
        session.add(
            ModelProbeSample(
                relay_id=relay_id,
                model_slug=slug,
                present=present,
                latency_ms=res.latency_ms if res.ok else None,
            )
        )
