async def uuid_to_str(uuid: str | int) -> str:
    if isinstance(uuid, int):
        return str(uuid)
    else:
        return uuid
