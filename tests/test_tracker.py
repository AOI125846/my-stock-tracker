from src.my_stock_tracker.tracker import fetch_chart_data

def test_fetch_stock_demo():
    res = fetch_chart_data("TST", "1d")
    assert isinstance(res, list)
    assert len(res) > 0
    assert "close" in res[0]
