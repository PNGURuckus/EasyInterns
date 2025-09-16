from typing import Optional, Any


async def verify_jwt_token(token: str) -> Optional[Any]:
    """Lightweight, patchable JWT verification stub.

    Tests patch this function to simulate auth. In default mode, it returns a
    simple object for non-empty tokens, and None for empty/obvious invalid values.
    """
    token = (token or "").strip()
    if not token:
        return None
    # Minimal fallback user object with an id attribute
    class _User:
        def __init__(self, id_: str):
            self.id = id_

    return _User("test-user-id")

