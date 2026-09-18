import re
from rapidfuzz.fuzz import ratio

from supabase_client import supabase


def normalize_text(text):
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def check_duplicate(
    employee_id,
    amount,
    expense_date,
    merchant,
    reason
):
    """
    Check historical claims for:
    1. High-confidence duplicates
    2. Possible duplicates with different expense dates
    """

    response = (
        supabase
        .table("claims")
        .select(
            "claim_id, employee_id, amount, expense_date, "
            "merchant, reason, status"
        )
        .eq("employee_id", employee_id)
        .execute()
    )

    existing_claims = response.data

    new_merchant = normalize_text(merchant)
    new_reason = normalize_text(reason)

    results = []

    for claim in existing_claims:

        existing_merchant = normalize_text(
            claim["merchant"]
        )

        existing_reason = normalize_text(
            claim["reason"]
        )

        merchant_score = ratio(
            new_merchant,
            existing_merchant
        )

        reason_score = ratio(
            new_reason,
            existing_reason
        )

        try:
            amount_difference = abs(
                float(amount) - float(claim["amount"])
            )

            amount_match = (
                amount_difference == 0
            )

        except (TypeError, ValueError):
            amount_match = False

        same_date = (
            str(claim["expense_date"])
            == str(expense_date)
        )

        # ------------------------------------------
        # HIGH-CONFIDENCE DUPLICATE
        # ------------------------------------------

        if (
            same_date
            and amount_match
            and merchant_score >= 80
            and reason_score >= 60
        ):
            results.append({
                "claim_id": claim["claim_id"],
                "classification": "BLOCK_DUPLICATE",
                "merchant_score": merchant_score,
                "reason_score": reason_score,
                "amount_match": True,
                "same_date": True,
                "status": claim["status"]
            })

        # ------------------------------------------
        # POSSIBLE DUPLICATE
        # Different date, but otherwise very similar
        # ------------------------------------------

        elif (
            not same_date
            and amount_match
            and merchant_score >= 80
            and reason_score >= 60
        ):
            results.append({
                "claim_id": claim["claim_id"],
                "classification": "POSSIBLE_DUPLICATE",
                "merchant_score": merchant_score,
                "reason_score": reason_score,
                "amount_match": True,
                "same_date": False,
                "status": claim["status"]
            })

    return results