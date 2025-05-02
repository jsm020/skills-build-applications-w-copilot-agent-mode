def make_auction_deeplink(auction_id: int, bot_username: str) -> str:
    return f"https://t.me/{bot_username}?start=auction_{auction_id}"

def parse_auction_deeplink(start_param: str) -> int | None:
    if start_param and start_param.startswith("auction_"):
        try:
            return int(start_param.split("_")[1])
        except Exception:
            return None
    return None
