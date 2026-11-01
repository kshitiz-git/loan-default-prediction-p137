"""Central settings: file paths, feature lists, seed and policy cut-offs used by every script."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # project folder
RAW_CSV = ROOT / "data" / "raw" / "credit_risk_dataset.csv"
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
CANDIDATES_DIR = MODELS / "candidates"
REPORTS = ROOT / "reports"
EDA_DIR = REPORTS / "eda"
LOG_DB = ROOT / "logs" / "predictions.db"

TARGET = "loan_status"                                 # 1 = defaulted, 0 = repaid
NUM = ["person_age", "person_income", "person_emp_length", "loan_amnt",
       "loan_int_rate", "loan_percent_income", "cb_person_cred_hist_length"]
CAT = ["person_home_ownership", "loan_intent", "loan_grade", "cb_person_default_on_file"]
FEATURES = NUM + CAT

SEED = 42
MODEL_VERSION = "v1"

APPROVE_BELOW = 0.20      # PD below this -> APPROVE (break-even PD at 11% interest and 45% LGD)
REJECT_FROM = 0.50        # PD at or above this -> REJECT; in between -> REVIEW by a loan officer
