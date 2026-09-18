from supabase_client import supabase
from datetime import datetime
from duplicate_detector import check_duplicate


def create_claim(
    employee_id,
    amount,
    expense_date,
    merchant,
    category,
    reason,
    receipt_text=None,
    receipt_url=None
):
    # Check for duplicates BEFORE creating the claim
    duplicates = check_duplicate(
    employee_id=employee_id,
    amount=amount,
    expense_date=expense_date,
    merchant=merchant,
    reason=reason
)

    blocked_duplicates = [
        duplicate
        for duplicate in duplicates
        if duplicate["classification"] == "BLOCK_DUPLICATE"
    ]

    possible_duplicates = [
        duplicate
        for duplicate in duplicates
        if duplicate["classification"] == "POSSIBLE_DUPLICATE"
    ]

    if blocked_duplicates:
        return {
            "success": False,
            "message": "Duplicate claim detected. Submission blocked.",
            "duplicates": blocked_duplicates
    }

    # Generate unique claim ID
    sequence_response = supabase.rpc(
        "get_next_claim_number"
    ).execute()

    claim_number = sequence_response.data
    claim_id = f"VSP-CLM-{claim_number:03d}"

    # Get employee's manager
    employee_response = (
    supabase
    .table("employees")
    .select("manager_id, role")
    .eq("employee_id", employee_id)
    .single()
    .execute()
)

    employee = employee_response.data

    manager_id = employee["manager_id"]
    role = employee["role"]

    if role == "manager":
        initial_status = "PENDING_FINANCE"
    else:
        initial_status = "PENDING_MANAGER"

    claim_data = {
    "claim_id": claim_id,
    "employee_id": employee_id,
    "amount": amount,
    "expense_date": expense_date,
    "claim_date": datetime.now().isoformat(),
    "merchant": merchant,
    "category": category,
    "reason": reason,
    "receipt_text": receipt_text,
    "receipt_url": receipt_url,
    "status": initial_status,
    "manager_id": manager_id,
    "duplicate_flag": bool(possible_duplicates),
    "duplicate_of_claim_id": (
        possible_duplicates[0]["claim_id"]
        if possible_duplicates
        else None
    )
}

    response = (
        supabase
        .table("claims")
        .insert(claim_data)
        .execute()
    )

    return {
        "success": True,
        "claim": response.data,
        "possible_duplicates": possible_duplicates
    }

def get_employee_claims(employee_id):
    response = (
        supabase
        .table("claims")
        .select("*")
        .eq("employee_id", employee_id)
        .order("claim_date", desc=True)
        .execute()
    )

    return response.data


def get_manager_pending_claims(manager_id):
    response = (
        supabase
        .table("claims")
        .select("*")
        .eq("manager_id", manager_id)
        .eq("status", "PENDING_MANAGER")
        .order("claim_date", desc=True)
        .execute()
    )

    return response.data


def approve_claim_by_manager(claim_id, manager_id):

    response = (
        supabase
        .table("claims")
        .select("*")
        .eq("claim_id", claim_id)
        .single()
        .execute()
    )

    claim = response.data

    # Make sure this claim belongs to this manager's team
    if claim["manager_id"] != manager_id:
        raise ValueError("You are not authorized to approve this claim.")

    # Prevent approval of a claim that is not waiting for manager approval
    if claim["status"] != "PENDING_MANAGER":
        raise ValueError("This claim is not pending manager approval.")

    # Prevent manager from approving their own claim
    if claim["employee_id"] == manager_id:
        raise ValueError("A manager cannot approve their own claim.")

    # Update claim
    updated = (
        supabase
        .table("claims")
        .update({
            "status": "PENDING_FINANCE",
            "manager_approved_at": datetime.now().isoformat()
        })
        .eq("claim_id", claim_id)
        .execute()
    )

    return updated.data


def reject_claim_by_manager(claim_id, manager_id, rejection_reason):

    response = (
        supabase
        .table("claims")
        .select("*")
        .eq("claim_id", claim_id)
        .single()
        .execute()
    )

    claim = response.data

    if claim["manager_id"] != manager_id:
        raise ValueError("You are not authorized to reject this claim.")

    if claim["status"] != "PENDING_MANAGER":
        raise ValueError("This claim is not pending manager approval.")

    if claim["employee_id"] == manager_id:
        raise ValueError("A manager cannot reject their own claim.")

    updated = (
        supabase
        .table("claims")
        .update({
            "status": "REJECTED_BY_MANAGER",
            "rejection_reason": rejection_reason,
            "rejected_by": manager_id,
            "rejected_at": datetime.now().isoformat()
        })
        .eq("claim_id", claim_id)
        .execute()
    )

    return updated.data


def get_finance_pending_claims():
    response = (
        supabase
        .table("claims")
        .select(
            "claim_id, employee_id, amount, expense_date, "
            "merchant, category, reason, receipt_text, receipt_url, "
            "status, manager_id, duplicate_flag, duplicate_of_claim_id, "
            "finance_question, finance_questioned_by, "
            "finance_questioned_at, finance_response, "
            "finance_responded_at, rejection_reason"
        )
        .eq("status", "PENDING_FINANCE")
        .order("expense_date", desc=True)
        .execute()
    )

    return response.data


def approve_and_reimburse_claim(claim_id, finance_id):
    response = (
        supabase
        .table("claims")
        .select("*")
        .eq("claim_id", claim_id)
        .single()
        .execute()
    )

    claim = response.data

    if claim.get("finance_question") and not claim.get("finance_response"):
        raise ValueError(
            "This claim has an unanswered Finance question."
        )

    if claim["status"] != "PENDING_FINANCE":
        raise ValueError(
            "This claim is not pending Finance approval."
        )

    if finance_id != "VSP-FIN-01":
        raise ValueError(
            "Only the Finance user can process reimbursement."
        )

    payment_number = claim_id.replace("VSP-CLM-", "")

    payment_id = f"VSP-PAY-{payment_number}"

    updated = (
        supabase
        .table("claims")
        .update({
            "status": "REIMBURSED",
            "finance_approved_at": datetime.now().isoformat(),
            "payment_id": payment_id,
            "payment_method": "Bank Transfer (Simulated)",
            "payment_date": datetime.now().isoformat()
        })
        .eq("claim_id", claim_id)
        .execute()
    )

    return updated.data

def reject_claim_by_finance(claim_id, finance_id, rejection_reason):
    response = (
        supabase.table("claims")
        .select("*")
        .eq("claim_id", claim_id)
        .single()
        .execute()
    )

    claim = response.data

    if claim.get("finance_question") and not claim.get("finance_response"):
        raise ValueError(
            "This claim has an unanswered Finance question."
        )

    if claim["status"] != "PENDING_FINANCE":
        raise ValueError("This claim is not pending Finance approval.")

    if finance_id != "VSP-FIN-01":
        raise ValueError("Only the Finance user can reject this claim.")

    if not rejection_reason or not rejection_reason.strip():
        raise ValueError("A rejection reason is required.")

    updated = (
        supabase.table("claims")
        .update({
            "status": "REJECTED_BY_FINANCE",
            "rejection_reason": rejection_reason.strip(),
            "rejected_by": finance_id,
            "rejected_at": datetime.now().isoformat()
        })
        .eq("claim_id", claim_id)
        .execute()
    )

    return updated.data

def question_claim_by_finance(claim_id, finance_id, question):
    response = (
        supabase.table("claims")
        .select("*")
        .eq("claim_id", claim_id)
        .single()
        .execute()
    )

    claim = response.data

    if claim["status"] != "PENDING_FINANCE":
        raise ValueError("This claim is not pending Finance approval.")

    if finance_id != "VSP-FIN-01":
        raise ValueError("Only the Finance user can question a claim.")

    if not question or not question.strip():
        raise ValueError("A question is required.")

    updated = (
        supabase.table("claims")
        .update({
            "finance_question": question.strip(),
            "finance_questioned_by": finance_id,
            "finance_questioned_at": datetime.now().isoformat()
        })
        .eq("claim_id", claim_id)
        .execute()
    )

    return updated.data

def respond_to_finance_question(claim_id, employee_id, response_text):

    response = (
        supabase
        .table("claims")
        .select("*")
        .eq("claim_id", claim_id)
        .single()
        .execute()
    )

    claim = response.data

    if not claim:
        raise ValueError("Claim not found.")

    if not claim.get("finance_question"):
        raise ValueError("This claim has not been questioned by Finance.")

    if claim["employee_id"] != employee_id:
        raise ValueError("Only the claimant can respond to this question.")

    if claim["status"] != "PENDING_FINANCE":
        raise ValueError("This claim is no longer pending Finance review.")

    if not response_text or not response_text.strip():
        raise ValueError("A response is required.")

    updated = (
        supabase
        .table("claims")
        .update({
            "finance_response": response_text.strip(),
            "finance_responded_at": datetime.now().isoformat()
        })
        .eq("claim_id", claim_id)
        .execute()
    )

    if not updated.data:
        raise ValueError("The Finance response was not saved to the database.")

    return updated.data[0]

def question_claim_by_manager(claim_id, manager_id, question):
    response = (
        supabase
        .table("claims")
        .select("*")
        .eq("claim_id", claim_id)
        .single()
        .execute()
    )

    claim = response.data

    if claim["status"] != "PENDING_MANAGER":
        raise ValueError(
            "This claim is not pending Manager approval."
        )

    if claim["manager_id"] != manager_id:
        raise ValueError(
            "You are not authorized to question this claim."
        )

    if not question or not question.strip():
        raise ValueError("A question is required.")

    updated = (
        supabase
        .table("claims")
        .update({
            "manager_question": question.strip(),
            "manager_questioned_by": manager_id,
            "manager_questioned_at": datetime.now().isoformat()
        })
        .eq("claim_id", claim_id)
        .execute()
    )

    return updated.data

def respond_to_manager_question(
    claim_id,
    employee_id,
    response_text
):
    response = (
        supabase
        .table("claims")
        .select("*")
        .eq("claim_id", claim_id)
        .single()
        .execute()
    )

    claim = response.data

    if not claim["manager_question"]:
        raise ValueError(
            "This claim has not been questioned by the Manager."
        )

    if claim["employee_id"] != employee_id:
        raise ValueError(
            "Only the claimant can respond to this question."
        )

    if claim["status"] != "PENDING_MANAGER":
        raise ValueError(
            "This claim is no longer pending Manager review."
        )

    if not response_text or not response_text.strip():
        raise ValueError("A response is required.")

    updated = (
        supabase
        .table("claims")
        .update({
            "manager_response": response_text.strip(),
            "manager_responded_at": datetime.now().isoformat()
        })
        .eq("claim_id", claim_id)
        .execute()
    )

    return updated.data

