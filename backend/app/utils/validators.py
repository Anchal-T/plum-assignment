import re
from datetime import date, timedelta

DOCTOR_REG_PATTERN = re.compile(r"^[A-Z]{2,4}/\d{4,6}/\d{4}$")
ALT_AYUR_PATTERN = re.compile(r"^AYUR/[A-Z]{2}/\d{4,6}/\d{4}$")

VALID_STATE_CODES = {
    "AP", "AR", "AS", "BR", "CG", "GA", "GJ", "HR", "HP", "JH", "KA", "KL",
    "MP", "MH", "MN", "ML", "MZ", "NL", "OD", "PB", "RJ", "SK", "TN", "TS",
    "TR", "UP", "UK", "WB", "DL", "JK", "LA", "PY", "CH", "AN", "DD", "DN",
    "AYUR",
}


def validate_doctor_reg(reg_number: str | None) -> bool:
    if not reg_number:
        return False
    if DOCTOR_REG_PATTERN.match(reg_number):
        state_code = reg_number.split("/")[0]
        return state_code in VALID_STATE_CODES
    if ALT_AYUR_PATTERN.match(reg_number):
        return True
    return False


def is_within_waiting_period(
    join_date: date | None,
    treatment_date: date,
    waiting_days: int,
) -> bool:
    if join_date is None:
        return False
    waiting_end = join_date + timedelta(days=waiting_days)
    return treatment_date < waiting_end


def check_submission_timeline(
    treatment_date: date,
    submission_date: date | None = None,
    max_days: int = 30,
) -> bool:
    if submission_date is None:
        submission_date = date.today()
    return (submission_date - treatment_date).days <= max_days
