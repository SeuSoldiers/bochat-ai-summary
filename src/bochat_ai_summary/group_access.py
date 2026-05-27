from __future__ import annotations


def is_group_allowed(
    group_id: str,
    group_code: str | None,
    whitelist: list[str],
    blacklist: list[str],
    blacklist_first: bool,
) -> bool:
    keys = {group_id}
    if group_code:
        keys.add(group_code)

    in_blacklist = any(item in keys for item in blacklist)
    in_whitelist = not whitelist or any(item in keys for item in whitelist)

    if blacklist_first:
        if in_blacklist:
            return False
        return in_whitelist

    if whitelist and not in_whitelist:
        return False
    return not in_blacklist
