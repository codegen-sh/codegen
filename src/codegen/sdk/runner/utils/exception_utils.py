from codegen.sdk.shared.exceptions.control_flow import StopCodemodException


def update_observation_meta(
    e: StopCodemodException,
    observation_meta: dict | None = None,
) -> dict:
    observation_meta = observation_meta or {}
    observation_meta.update(
        {
            "stop_codemod_exception_type": e.__class__.__name__,
            "threshold": e.threshold,
        },
    )
    return observation_meta
