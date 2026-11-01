"""Request and response shapes. Pydantic rejects bad input with HTTP 422 before the model sees it."""
from typing import Literal, Optional
from pydantic import BaseModel, Field


class LoanApplication(BaseModel):
    person_age: int = Field(..., ge=18, le=100, examples=[28])
    person_income: float = Field(..., gt=0, le=10_000_000, examples=[42000])
    person_home_ownership: Literal["RENT", "OWN", "MORTGAGE", "OTHER"] = Field(..., examples=["RENT"])
    person_emp_length: Optional[float] = Field(None, ge=0, le=60, description="Years employed; null if unknown")
    loan_intent: Literal["EDUCATION", "MEDICAL", "VENTURE", "PERSONAL",
                         "DEBTCONSOLIDATION", "HOMEIMPROVEMENT"] = Field(..., examples=["MEDICAL"])
    loan_grade: Literal["A", "B", "C", "D", "E", "F", "G"] = Field(..., examples=["C"])
    loan_amnt: float = Field(..., gt=0, le=1_000_000, examples=[12000])
    loan_int_rate: Optional[float] = Field(None, ge=0, le=40, description="Annual %; null if not priced yet")
    cb_person_default_on_file: Literal["Y", "N"] = Field(..., examples=["N"])
    cb_person_cred_hist_length: int = Field(..., ge=0, le=60, examples=[4])


class Reason(BaseModel):
    feature: str
    value: Optional[float | str]
    impact: float                     # SHAP value in log-odds; positive pushes towards default
    text: str                         # plain-language reason


class ScoreResponse(BaseModel):
    application_id: str
    probability_of_default: float
    risk_band: Literal["low", "medium", "high"]
    decision: Literal["APPROVE", "REVIEW", "REJECT"]
    top_reasons: list[Reason]
    model_version: str
    latency_ms: float
