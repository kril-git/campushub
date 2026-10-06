def truncate(text: str, limit: int = 200) -> str:
    return text[:limit] if len(text) > limit else text
