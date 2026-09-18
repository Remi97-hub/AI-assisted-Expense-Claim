from supabase_client import supabase


APPROVED_STATUSES = [
    "APPROVED_BY_FINANCE",
    "REIMBURSED"
]

REJECTED_STATUSES = [
    "REJECTED_BY_MANAGER",
    "REJECTED_BY_FINANCE"
]


def get_monthly_claims(start_date, end_date):
    """
    Get approved/reimbursed claims for the selected period.
    These represent actual expenses.
    """

    response = (
        supabase
        .table("claims")
        .select(
            "claim_id, employee_id, amount, expense_date, "
            "merchant, category, status"
        )
        .gte("expense_date", start_date)
        .lte("expense_date", end_date)
        .in_("status", APPROVED_STATUSES)
        .order("expense_date", desc=True)
        .execute()
    )

    return response.data


def get_rejected_claims(start_date, end_date):
    """
    Get rejected claims separately.
    """

    response = (
        supabase
        .table("claims")
        .select(
            "claim_id, employee_id, amount, expense_date, "
            "merchant, category, status, rejection_reason"
        )
        .gte("expense_date", start_date)
        .lte("expense_date", end_date)
        .in_("status", REJECTED_STATUSES)
        .order("expense_date", desc=True)
        .execute()
    )

    return response.data


def get_total_expense(start_date, end_date):
    """
    Total actual expense from approved/reimbursed claims.
    """

    claims = get_monthly_claims(start_date, end_date)

    return sum(
        float(claim["amount"])
        for claim in claims
    )


def get_total_claims(start_date, end_date):
    """
    Number of approved/reimbursed claims.
    """

    claims = get_monthly_claims(start_date, end_date)

    return len(claims)


def get_expense_by_employee(start_date, end_date):
    """
    Actual expense grouped by employee.
    """

    claims = get_monthly_claims(start_date, end_date)

    employee_expenses = {}

    for claim in claims:
        employee_id = claim["employee_id"]

        employee_expenses[employee_id] = (
            employee_expenses.get(employee_id, 0)
            + float(claim["amount"])
        )

    return dict(
        sorted(
            employee_expenses.items(),
            key=lambda item: item[1],
            reverse=True
        )
    )


def get_expense_by_category(start_date, end_date):
    """
    Actual expense grouped by category.
    """

    claims = get_monthly_claims(start_date, end_date)

    category_expenses = {}

    for claim in claims:
        category = claim["category"]

        category_expenses[category] = (
            category_expenses.get(category, 0)
            + float(claim["amount"])
        )

    return dict(
        sorted(
            category_expenses.items(),
            key=lambda item: item[1],
            reverse=True
        )
    )


def get_employee_category_expense(start_date, end_date):
    """
    Actual expense grouped by employee and category.
    """

    claims = get_monthly_claims(start_date, end_date)

    spending = {}

    for claim in claims:

        employee_id = claim["employee_id"]
        category = claim["category"]
        amount = float(claim["amount"])

        key = (employee_id, category)

        spending[key] = (
            spending.get(key, 0) + amount
        )

    result = []

    for (employee_id, category), amount in spending.items():

        result.append({
            "employee_id": employee_id,
            "category": category,
            "amount": amount
        })

    return sorted(
        result,
        key=lambda item: item["amount"],
        reverse=True
    )


def get_rejection_summary(start_date, end_date):
    """
    Summary of rejected claims.
    """

    claims = get_rejected_claims(
        start_date,
        end_date
    )

    rejected_count = len(claims)

    rejected_amount = sum(
        float(claim["amount"])
        for claim in claims
    )

    approved_count = get_total_claims(
        start_date,
        end_date
    )

    total_decided = approved_count + rejected_count

    if total_decided == 0:
        rejection_rate = 0
    else:
        rejection_rate = (
            rejected_count / total_decided
        ) * 100

    return {
        "rejected_count": rejected_count,
        "rejected_amount": round(rejected_amount, 2),
        "rejection_rate": round(rejection_rate, 2)
    }


def get_daily_expense(start_date, end_date):
    """
    Daily actual expense trend.
    """

    claims = get_monthly_claims(
        start_date,
        end_date
    )

    daily_expense = {}

    for claim in claims:

        date = str(claim["expense_date"])
        amount = float(claim["amount"])

        daily_expense[date] = (
            daily_expense.get(date, 0) + amount
        )

    return dict(sorted(daily_expense.items()))

def get_employee_monthly_spending_with_limit(start_date, end_date):
    claims = get_monthly_claims(start_date, end_date)

    employee_spending = {}

    for claim in claims:
        employee_id = claim["employee_id"]
        amount = float(claim["amount"])

        employee_spending[employee_id] = (
            employee_spending.get(employee_id, 0) + amount
        )

    # Get Staff and Manager employees only
    response = (
        supabase
        .table("employees")
        .select("employee_id, name, role, monthly_limit")
        .in_("role", ["staff", "manager"])
        .execute()
    )

    employees = response.data

    result = []

    for employee in employees:
        employee_id = employee["employee_id"]

        spending = employee_spending.get(employee_id, 0)
        monthly_limit = float(employee["monthly_limit"])

        if monthly_limit > 0:
            utilization = (spending / monthly_limit) * 100
            remaining = monthly_limit - spending
        else:
            utilization = 0
            remaining = 0

        result.append({
            "employee_id": employee_id,
            "name": employee["name"],
            "role": employee["role"],
            "spending": round(spending, 2),
            "monthly_limit": round(monthly_limit, 2),
            "remaining": round(remaining, 2),
            "utilization": round(utilization, 2),
            "exceeded": spending >= monthly_limit
        })

    return sorted(
        result,
        key=lambda item: item["spending"],
        reverse=True
    )

    