import pandas as pd


def test_factors_have_sources():
    df = pd.read_csv("data/emission_factors.csv")
    assert not df.empty
    assert df["source"].notna().all()
    assert df["factor"].gt(0).all()
