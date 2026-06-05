from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.utils.validators import validate_doctor_reg, is_within_waiting_period, check_submission_timeline
from app.utils.constants import RejectionCode


def _to_decimal(v: Any) -> Decimal:
    return Decimal(str(v))


def _to_date(v: Any) -> date | None:
    if v is None:
        return None
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v))


class RuleEngine:
    """5-step adjudication pipeline. Pure logic, no I/O."""

    def __init__(self, policy: dict, settings=None):
        self.policy = policy
        self.cov = policy["coverage_details"]
        self.wait = policy["waiting_periods"]
        self.exclusions_raw = [e.lower() for e in policy["exclusions"]]
        self.claim_req = policy["claim_requirements"]
        self.network = [h.lower() for h in policy.get("network_hospitals", [])]

        self.annual_limit = _to_decimal(self.cov["annual_limit"])
        self.per_claim_limit = _to_decimal(self.cov["per_claim_limit"])
        self.min_claim = _to_decimal(self.claim_req["minimum_claim_amount"])
        self.submission_days = self.claim_req["submission_timeline_days"]

        if settings is not None:
            self.confidence_threshold = settings.confidence_threshold
            self.high_value_threshold = _to_decimal(str(settings.manual_review_amount_threshold))
            self.fraud_same_day_threshold = settings.fraud_same_day_threshold
            self.fraud_frequency_threshold = settings.fraud_frequency_threshold
        else:
            self.confidence_threshold = 0.70
            self.high_value_threshold = _to_decimal("25000")
            self.fraud_same_day_threshold = 2
            self.fraud_frequency_threshold = 5

    def adjudicate(
        self,
        member: dict,
        claim: dict,
        docs: list[dict],
        fraud_context: dict | None = None,
    ) -> dict:
        merged = self._merge_extractions(docs)
        steps = []
        rejection_reasons = []

        s1 = self._check_eligibility(member, claim, merged)
        steps.append(s1)
        rejection_reasons.extend(s1.get("rejection_codes", []))

        s2 = self._validate_documents(docs, merged)
        steps.append(s2)
        rejection_reasons.extend(s2.get("rejection_codes", []))

        s3 = self._verify_coverage(merged)
        steps.append(s3)
        rejection_reasons.extend(s3.get("rejection_codes", []))

        s4 = self._validate_limits(claim, merged)
        steps.append(s4)
        rejection_reasons.extend(s4.get("rejection_codes", []))

        s5 = self._review_medical_necessity(merged)
        steps.append(s5)
        rejection_reasons.extend(s5.get("rejection_codes", []))

        fraud_flags = self._check_fraud(fraud_context)

        decision = self._compute_decision(steps, merged, claim, fraud_flags)
        decision["steps"] = steps
        decision["rejection_reasons"] = list(set(rejection_reasons))
        decision["fraud_flags"] = fraud_flags
        return decision

    # ------------------------------------------------------------------
    # Merging
    # ------------------------------------------------------------------

    def _merge_extractions(self, docs: list[dict]) -> dict:
        presc = None
        bill = None
        confidences = []

        for d in docs:
            confidences.append(d.get("confidence", 0.0))
            if d["doc_type"] == "prescription":
                presc = d.get("fields", {})
            elif d["doc_type"] == "bill":
                bill = d.get("fields", {})

        return {
            "has_prescription": presc is not None,
            "doctor_name": (presc or {}).get("doctor_name"),
            "doctor_reg": (presc or {}).get("doctor_reg"),
            "diagnosis": ((presc or {}).get("diagnosis") or "").strip(),
            "medicines": (presc or {}).get("medicines", []),
            "tests_prescribed": (presc or {}).get("tests_prescribed", []),
            "procedures": (presc or {}).get("procedures", []),
            "treatment": ((presc or {}).get("treatment") or "").strip(),
            "line_items": (bill or {}).get("line_items", []),
            "total_amount": _to_decimal((bill or {}).get("total", 0)),
            "avg_confidence": (
                sum(confidences) / len(confidences) if confidences else 0.0
            ),
        }

    # ------------------------------------------------------------------
    # Step 1: Eligibility
    # ------------------------------------------------------------------

    DISEASE_WAITING_MAP = {
        "diabetes": 90,
        "hypertension": 90,
        "joint replacement": 730,
        "pre-existing": 365,
    }

    def _check_eligibility(self, member: dict, claim: dict, merged: dict) -> dict:
        codes = []
        treatment_date = _to_date(claim["treatment_date"])
        join_date = _to_date(member.get("join_date"))
        diagnosis = (merged.get("diagnosis") or "").lower()

        if member.get("status") != "active":
            codes.append(RejectionCode.POLICY_INACTIVE)

        effective = _to_date(self.policy.get("effective_date"))
        if effective and treatment_date and treatment_date < effective:
            codes.append(RejectionCode.POLICY_INACTIVE)

        if join_date and treatment_date:
            initial_wait = self.wait.get("initial_waiting", 30)
            if is_within_waiting_period(join_date, treatment_date, initial_wait):
                codes.append(RejectionCode.WAITING_PERIOD)

            for disease, days in self.DISEASE_WAITING_MAP.items():
                if disease in diagnosis and is_within_waiting_period(
                    join_date, treatment_date, days
                ):
                    codes.append(RejectionCode.WAITING_PERIOD)
                    break

        submission_date = _to_date(claim.get("submission_date")) if claim.get("submission_date") else None
        if treatment_date and submission_date and not check_submission_timeline(
            treatment_date, submission_date, max_days=self.submission_days
        ):
            codes.append(RejectionCode.LATE_SUBMISSION)

        if codes:
            return self._step_result("eligibility", "FAIL", codes)
        return self._step_result("eligibility", "PASS", [])

    # ------------------------------------------------------------------
    # Step 2: Document Validation
    # ------------------------------------------------------------------

    LEGIBILITY_THRESHOLD = 0.5

    def _validate_documents(self, docs: list[dict], merged: dict) -> dict:
        codes = []

        if not merged["has_prescription"]:
            codes.append(RejectionCode.MISSING_DOCUMENTS)

        if merged["doctor_reg"]:
            if not validate_doctor_reg(merged["doctor_reg"]):
                codes.append(RejectionCode.DOCTOR_REG_INVALID)
        elif merged["has_prescription"]:
            codes.append(RejectionCode.DOCTOR_REG_INVALID)

        if merged["avg_confidence"] < self.LEGIBILITY_THRESHOLD:
            codes.append(RejectionCode.ILLEGIBLE_DOCUMENTS)

        dates = set()
        for d in docs:
            f = d.get("fields", {})
            dt = f.get("date") or f.get("treatment_date")
            if dt:
                dates.add(str(dt))
        if len(dates) > 1:
            codes.append(RejectionCode.DATE_MISMATCH)

        if codes:
            return self._step_result("document_validation", "FAIL", codes)
        return self._step_result("document_validation", "PASS", [])

    # ------------------------------------------------------------------
    # Step 3: Coverage Verification
    # ------------------------------------------------------------------

    PRE_AUTH_TESTS = {"mri", "ct scan", "ct-scan"}
    COSMETIC_KEYWORDS = [
        "whitening", "cosmetic", "aesthetic", "botox",
        "liposuction", "hair transplant",
    ]

    # Kept adjacent to the method that uses it for readability.
    EXCLUSION_SYNONYMS = {
        "weight loss treatments": ["obesity", "overweight", "bmi", "bariatric"],
    }

    def _verify_coverage(self, merged: dict) -> dict:
        codes = []
        excluded_item_descriptions = []
        diagnosis_lower = merged.get("diagnosis", "").lower()
        treatment_lower = merged.get("treatment", "").lower()
        all_text = f"{diagnosis_lower} {treatment_lower}"

        for raw_exclusion in self.exclusions_raw:
            if self._text_matches_exclusion(all_text, raw_exclusion):
                codes.append(RejectionCode.SERVICE_NOT_COVERED)
                # Diagnosis-level exclusion → full rejection, no partial items.
                return self._step_result("coverage_verification", "FAIL", codes,
                                         excluded_items=None)

        for item in merged.get("line_items", []):
            desc = item.get("description", "").lower()
            if any(kw in desc for kw in self.COSMETIC_KEYWORDS):
                excluded_item_descriptions.append(item["description"])

        if excluded_item_descriptions:
            all_excluded = len(excluded_item_descriptions) >= len(merged.get("line_items", []))
            if all_excluded:
                codes.append(RejectionCode.SERVICE_NOT_COVERED)
                return self._step_result("coverage_verification", "FAIL", codes,
                                         excluded_items=None)
            return self._step_result("coverage_verification", "WARN",
                                     [RejectionCode.SERVICE_NOT_COVERED],
                                     excluded_items=excluded_item_descriptions)

        if self._needs_pre_auth(merged):
            codes.append(RejectionCode.PRE_AUTH_MISSING)

        if codes:
            return self._step_result("coverage_verification", "FAIL", codes,
                                     excluded_items=None)
        return self._step_result("coverage_verification", "PASS", [],
                                 excluded_items=None)

    def _text_matches_exclusion(self, text: str, exclusion: str) -> bool:
        if exclusion in text:
            return True
        synonyms = self.EXCLUSION_SYNONYMS.get(exclusion, [])
        return any(s in text for s in synonyms)

    def _needs_pre_auth(self, merged: dict) -> bool:
        for test in merged.get("tests_prescribed", []):
            tl = test.lower()
            if any(pa in tl for pa in self.PRE_AUTH_TESTS):
                return True
        return False

    # ------------------------------------------------------------------
    # Step 4: Limit Validation
    # ------------------------------------------------------------------

    def _validate_limits(self, claim: dict, merged: dict) -> dict:
        codes = []
        claim_amount = _to_decimal(claim["claim_amount"])

        if claim_amount < self.min_claim:
            codes.append(RejectionCode.BELOW_MIN_AMOUNT)

        if claim_amount > self.per_claim_limit:
            codes.append(RejectionCode.PER_CLAIM_EXCEEDED)

        if codes:
            return self._step_result("limit_validation", "FAIL", codes)
        return self._step_result("limit_validation", "PASS", [])

    # ------------------------------------------------------------------
    # Step 5: Medical Necessity
    # ------------------------------------------------------------------

    def _review_medical_necessity(self, merged: dict) -> dict:
        diagnosis = merged.get("diagnosis", "").lower()

        if not diagnosis:
            return self._step_result("medical_necessity", "FAIL",
                                     [RejectionCode.NOT_MEDICALLY_NECESSARY])

        for kw in self.COSMETIC_KEYWORDS:
            if kw in diagnosis:
                return self._step_result("medical_necessity", "FAIL",
                                         [RejectionCode.COSMETIC_PROCEDURE])

        experimental = ["experimental", "trial", "investigational"]
        for kw in experimental:
            if kw in diagnosis:
                return self._step_result("medical_necessity", "FAIL",
                                         [RejectionCode.EXPERIMENTAL_TREATMENT])

        return self._step_result("medical_necessity", "PASS", [])

    # ------------------------------------------------------------------
    # Fraud
    # ------------------------------------------------------------------

    def _check_fraud(self, ctx: dict | None) -> list[str]:
        flags = []
        if not ctx:
            return flags
        prev = ctx.get("previous_claims_same_day", 0)
        if prev >= self.fraud_same_day_threshold:
            flags.append(f"Multiple claims same day ({prev + 1} total)")
        frequency = ctx.get("claims_last_30_days", 0)
        if frequency >= self.fraud_frequency_threshold:
            flags.append(f"Unusual claim frequency ({frequency} in 30 days)")
        return flags

    # ------------------------------------------------------------------
    # Copay & Discount
    # ------------------------------------------------------------------

    def _get_primary_category(self, merged: dict) -> str | None:
        cat_totals: dict[str, Decimal] = {}
        for item in merged.get("line_items", []):
            cat = item.get("category", "") or ""
            amount = _to_decimal(item.get("amount", 0))
            cat_totals[cat] = cat_totals.get(cat, Decimal("0")) + amount
        if not cat_totals:
            return None
        return max(cat_totals, key=cat_totals.get)

    def _calculate_copay(self, claim: dict, merged: dict) -> Decimal:
        primary = self._get_primary_category(merged)
        if primary is None:
            return Decimal("0")
        total = _to_decimal(claim["claim_amount"])

        if primary == "consultation":
            pct = self.cov.get("consultation_fees", {}).get("copay_percentage", 10)
            return total * _to_decimal(pct) / Decimal("100")

        if primary == "pharmacy":
            has_branded = any(
                not item.get("is_generic", True)
                for item in merged.get("line_items", [])
                if (item.get("category") or "") == "pharmacy"
            )
            if has_branded:
                pct = self.cov.get("pharmacy", {}).get("branded_drugs_copay", 30)
                return total * _to_decimal(pct) / Decimal("100")

        return Decimal("0")

    def _calculate_network_discount(self, claim: dict) -> Decimal:
        hospital = (claim.get("hospital_name") or "").lower()
        if hospital in self.network:
            pct = self.cov.get("consultation_fees", {}).get("network_discount", 20)
            return _to_decimal(claim["claim_amount"]) * _to_decimal(pct) / Decimal("100")
        return Decimal("0")

    # ------------------------------------------------------------------
    # Decision Computation (Priority: fraud > exclusions > limits > docs > eligibility)
    # ------------------------------------------------------------------

    def _compute_decision(
        self,
        steps: list[dict],
        merged: dict,
        claim: dict,
        fraud_flags: list[str],
    ) -> dict:
        claim_amount = _to_decimal(claim["claim_amount"])
        discount = self._calculate_network_discount(claim)
        avg_conf = merged.get("avg_confidence", 0.5)

        statuses = {s["step"]: s["status"] for s in steps}
        has_fail = any(s == "FAIL" for s in statuses.values())
        coverage_step = next(
            (s for s in steps if s["step"] == "coverage_verification"), {}
        )
        has_excluded_items = coverage_step.get("has_excluded_items", False)

        if fraud_flags:
            return self._make_decision(
                "MANUAL_REVIEW", Decimal("0"), Decimal("0"), discount,
                min(avg_conf, 0.65),
                "Fraud indicators detected. Manual review required.", claim,
            )

        if avg_conf < self.confidence_threshold:
            return self._make_decision(
                "MANUAL_REVIEW", Decimal("0"), Decimal("0"), discount,
                avg_conf, "Low confidence. Manual review required.", claim,
            )

        if claim_amount > self.high_value_threshold:
            return self._make_decision(
                "MANUAL_REVIEW", Decimal("0"), Decimal("0"), discount,
                avg_conf, "High-value claim. Manual review required.", claim,
            )

        if has_excluded_items:
            rejected_total = sum(
                _to_decimal(item.get("amount", 0))
                for item in merged.get("line_items", [])
                if self._is_cosmetic_item(item)
            )
            approved = claim_amount - rejected_total
            copay = self._calculate_copay({"claim_amount": str(approved)}, merged)
            return self._make_decision(
                "PARTIAL", max(approved - copay, Decimal("0")), copay, discount,
                avg_conf,
                f"Partial approval. Excluded items: ₹{rejected_total}.", claim,
            )

        if has_fail:
            return self._make_decision(
                "REJECTED", Decimal("0"), Decimal("0"), discount,
                avg_conf, "Claim rejected. See rejection reasons.", claim,
            )

        copay = self._calculate_copay(claim, merged)
        if discount > 0:
            approved = claim_amount - discount
        else:
            approved = claim_amount - copay

        notes = "All checks passed."
        if discount > 0:
            notes += f" Network discount applied: ₹{discount}."
        if copay > 0:
            notes += f" Co-pay deducted: ₹{copay}."

        return self._make_decision(
            "APPROVED", max(approved, Decimal("0")), copay, discount,
            avg_conf, notes, claim,
        )

    def _is_cosmetic_item(self, item: dict) -> bool:
        desc = item.get("description", "").lower()
        return any(kw in desc for kw in self.COSMETIC_KEYWORDS)

    def _make_decision(
        self, decision: str, approved_amount: Decimal, copay: Decimal,
        discount: Decimal, confidence: float, notes: str, claim: dict,
    ) -> dict:
        is_cashless = claim.get("is_cashless", False)
        cashless_approved = is_cashless and discount > 0

        next_steps_map = {
            "APPROVED": (
                f"Amount of ₹{approved_amount} will be reimbursed within 5-7 business days."
                if not cashless_approved
                else f"Cashless approval granted. ₹{approved_amount} settled directly."
            ),
            "REJECTED": "You may appeal this decision or contact support.",
            "PARTIAL": "Approved amount will be disbursed. Rejected items may be appealed.",
            "MANUAL_REVIEW": "Claim has been flagged for manual review. Our team will contact you.",
        }

        return {
            "decision": decision,
            "approved_amount": approved_amount,
            "copay_amount": copay,
            "network_discount": discount,
            "cashless_approved": cashless_approved,
            "rejection_reasons": [],
            "confidence_score": round(confidence, 2),
            "notes": notes,
            "next_steps": next_steps_map.get(decision, ""),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _step_result(self, step: str, status: str, codes: list[str],
                     excluded_items: list[str] | None = None) -> dict:
        detail_map = {
            "eligibility": "Policy active, member covered",
            "document_validation": "All documents valid",
            "coverage_verification": "All services covered",
            "limit_validation": "Within limits",
            "medical_necessity": "Medical necessity established",
        }
        detail = detail_map.get(step, "")
        if codes:
            detail = f"{status}: {', '.join(str(c) for c in codes)}"
        return {
            "step": step,
            "status": status,
            "detail": detail,
            "rejection_codes": codes,
            "has_excluded_items": bool(excluded_items),
            "excluded_items": excluded_items or [],
        }
