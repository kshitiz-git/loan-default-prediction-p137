"""Writes the two CSV deliverables: dataset.csv (cleaned data, original column order) and data_dictionary.csv.
Run from the project root with the project venv:  .\\.venv\\Scripts\\python.exe -m submission.build.build_data_files"""
import csv
import pandas as pd
from src.config import ROOT
from src.data_prep import load_and_clean, load_raw

OUT = ROOT / "submission" / "final"

TYPES = {"person_age": "int", "person_income": "int", "person_home_ownership": "category",
         "person_emp_length": "float", "loan_intent": "category", "loan_grade": "category", "loan_amnt": "int",
         "loan_int_rate": "float", "loan_status": "int", "loan_percent_income": "float",
         "cb_person_default_on_file": "category", "cb_person_cred_hist_length": "int"}

DESCRIPTIONS = {
    "person_age": "Applicant's age in whole years at application time. 20 to 94 after cleaning; the 5 raw rows above 100 (including ages 123 and 144) were removed as data-entry errors. The API accepts 18 to 100.",
    "person_income": "Applicant's annual income in the dataset's currency units (whole number, 4,000 to 2,039,784). Strongest single driver of predicted risk (mean |SHAP| 0.92).",
    "person_home_ownership": "Housing status: RENT, MORTGAGE, OWN or OTHER. Used as a category; renters default more often in this data.",
    "person_emp_length": "Years in the current job, decimal, 0 to 41 after cleaning (2 raw rows above 60 removed). 887 rows are empty; the model fills them with the training median, so the column is nullable.",
    "loan_intent": "Purpose of the loan: EDUCATION, MEDICAL, VENTURE, PERSONAL, DEBTCONSOLIDATION or HOMEIMPROVEMENT. Raw default rate ranges from 14.8% (VENTURE) to 28.6% (DEBTCONSOLIDATION).",
    "loan_grade": "Lender's own risk grade from A (best) to G (worst). Raw default rate rises from 10.0% in grade A to 98.4% in grade G. Used as the baseline approval rule in the NPA back-test.",
    "loan_amnt": "Loan amount requested, whole number, 500 to 35,000. Used as the weight in the NPA ratio by amount.",
    "loan_int_rate": "Annual interest rate offered, percent with 2 decimals, 5.42 to 23.22. 3,094 rows are empty (rate not priced yet); the model fills them with the training median, so the column is nullable.",
    "loan_status": "Target label: 1 if the loan defaulted, 0 if it was repaid. 7,088 of the 32,409 cleaned rows are 1 (21.9%). This is what the model predicts as a probability of default (PD).",
    "loan_percent_income": "loan_amnt divided by person_income, 2 decimals, 0.00 to 0.83. Highest correlation with default (0.38). The scoring API computes it itself; clients never send it.",
    "cb_person_default_on_file": "Y if the credit bureau file shows a past default, N if not.",
    "cb_person_cred_hist_length": "Length of the applicant's credit history in whole years, 2 to 30.",
}


def write_dictionary(df: pd.DataFrame) -> None:
    rows = []
    for col in df.columns:
        samples = []
        for v in df[col].head(3):
            if pd.isna(v):
                samples.append("")
            elif TYPES[col] == "float":
                samples.append(f"{v:.2f}")
            else:
                samples.append(str(v))
        rows.append([col, TYPES[col], *samples, "Yes" if df[col].isna().any() else "No", DESCRIPTIONS[col]])
    with open(OUT / "data_dictionary.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["column_name", "data_type", "sample_value_1", "sample_value_2", "sample_value_3", "nullable",
                    "description"])
        w.writerows(rows)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    raw_order = list(load_raw().columns)                      # keep the Kaggle file's column order
    clean = load_and_clean()[raw_order]
    clean.to_csv(OUT / "dataset.csv", index=False, encoding="utf-8", lineterminator="\n")
    write_dictionary(clean)
    print(f"dataset.csv {clean.shape}, defaults {int(clean['loan_status'].sum())}, "
          f"missing {clean.isna().sum()[clean.isna().sum() > 0].to_dict()}")
    print(clean.describe().loc[["min", "max"]].T.to_string())
