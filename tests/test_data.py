import pandas as pd
from src.config import PROCESSED, TARGET
from src.data_prep import load_and_clean


def test_cleaning_removes_impossible_rows():
    df = load_and_clean()
    assert len(df) == 32409
    assert df["person_age"].max() <= 100
    assert not (df["person_emp_length"] > 60).any()
    assert df.duplicated().sum() == 0


def test_splits_are_stratified_and_disjoint():
    parts = [pd.read_csv(PROCESSED / f"{n}.csv") for n in ("train", "val", "test")]
    assert [len(p) for p in parts] == [22686, 4861, 4862]
    rates = [p[TARGET].mean() for p in parts]
    assert max(rates) - min(rates) < 0.005                    # same default rate in every split
    assert pd.concat(parts).duplicated().sum() == 0            # no loan appears in two splits
