import json


def sse_event(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"
