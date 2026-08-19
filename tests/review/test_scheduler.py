from meridian.review import scheduler


def test_pass_grows_interval() -> None:
    interval, ease = scheduler.next_interval(interval=3.0, ease=2.5, grade="got_it")
    assert interval > 3.0


def test_miss_resets_interval_to_short() -> None:
    interval, ease = scheduler.next_interval(interval=16.0, ease=2.5, grade="missed")
    assert interval <= 1.0


def test_partial_grows_less_than_pass() -> None:
    p, _ = scheduler.next_interval(3.0, 2.5, "got_it")
    q, _ = scheduler.next_interval(3.0, 2.5, "partial")
    assert q < p
