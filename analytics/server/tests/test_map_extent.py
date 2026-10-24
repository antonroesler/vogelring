"""Map extent: far-away outliers must not shrink the bulk of the points to a dot."""

from vogelring_analytics.maps import core_bounds


def test_core_bounds_keeps_bulk_and_counts_outliers():
    lats = [50.10 + i * 0.001 for i in range(100)] + [52.5]  # Frankfurt cluster + one point in Britain-ish latitude
    lons = [8.68 + i * 0.001 for i in range(100)] + [-1.5]
    bounds, outside = core_bounds(lats, lons)
    assert outside == 1
    assert 50.0 < bounds[0][0] < bounds[1][0] < 50.3 and 8.6 < bounds[0][1] < bounds[1][1] < 8.9


def test_core_bounds_keeps_everything_when_spread_is_real():
    lats = [50.1 + i * 0.001 for i in range(60)] + [52.3 + i * 0.001 for i in range(40)]  # two real clusters
    lons = [8.68 + i * 0.001 for i in range(60)] + [4.9 + i * 0.001 for i in range(40)]
    bounds, outside = core_bounds(lats, lons)
    assert outside == 0 and bounds[0][0] <= 50.1 and bounds[1][0] >= 52.3


def test_core_bounds_small_sets_untouched():
    bounds, outside = core_bounds([50.1, 50.2, 55.0], [8.6, 8.7, -1.0])
    assert outside == 0 and bounds == [[50.1, -1.0], [55.0, 8.7]]
