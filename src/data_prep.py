"""Phase 3: load the raw Kaggle CSV, remove impossible rows, and make stratified train/val/test splits."""
import pandas as pd
from sklearn.model_selection import train_test_split
from src.config import RAW_CSV, PROCESSED, TARGET, FEATURES, SEED

RAW_COLUMNS = FEATURES + [TARGET]


def load_raw(path=RAW_CSV) -> pd.DataFrame:
    """Read the raw CSV; fail loudly if it is missing or a column is absent."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Download 'Credit Risk Dataset' by laotse from Kaggle "
            "(https://www.kaggle.com/datasets/laotse/credit-risk-dataset) and save it as "
            "data/raw/credit_risk_dataset.csv")
    df = pd.read_csv(path, encoding="utf-8")
    missing = [c for c in RAW_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Raw CSV is missing columns: {missing}")
    return df


def load_and_clean(path=RAW_CSV) -> pd.DataFrame:
    """Apply the three cleaning rules in a fixed order. Missing values stay: the pipelines impute them."""
    df = load_raw(path)
    before = len(df)
    df = df.drop_duplicates()                           # exact duplicate rows add no information
    df = df[df["person_age"] <= 100]                    # ages 123 and 144 are data-entry errors
    df = df[~(df["person_emp_length"] > 60)]            # >60 years in one job is impossible; NaN is kept
    print(f"Cleaning: {before} rows -> {len(df)} rows")
    return df[FEATURES + [TARGET]].reset_index(drop=True)


def split(df: pd.DataFrame):
    """70/15/15 split, stratified on the target so every part has the same default rate."""
    train, rest = train_test_split(df, test_size=0.30, stratify=df[TARGET], random_state=SEED)
    val, test = train_test_split(rest, test_size=0.50, stratify=rest[TARGET], random_state=SEED)
    return train, val, test


if __name__ == "__main__":
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, part in zip(("train", "val", "test"), split(load_and_clean())):
        part.to_csv(PROCESSED / f"{name}.csv", index=False, encoding="utf-8")
        print(f"{name}: {len(part)} rows, default rate {part[TARGET].mean():.3f}")
