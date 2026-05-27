from bochat_ai_summary.group_access import is_group_allowed


def test_whitelist_hit():
    assert is_group_allowed("g1", "TECH001", ["g1"], [], True)


def test_blacklist_hit():
    assert not is_group_allowed("g1", "TECH001", [], ["g1"], True)


def test_blacklist_first_on_conflict():
    assert not is_group_allowed("g1", "TECH001", ["g1"], ["g1"], True)


def test_allow_when_whitelist_empty_and_not_blacklisted():
    assert is_group_allowed("g1", "TECH001", [], [], True)
