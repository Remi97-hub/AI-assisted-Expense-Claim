# Expense Claims

An AI-assisted expense claim management system for Staff, Managers, and
Finance.

The application covers the complete claim lifecycle:

**Receipt/Text → AI extraction → Employee review → Duplicate check →
Manager approval → Finance approval → Simulated reimbursement**

Managers can also submit their own expenses. Manager self-claims bypass
manager approval and go directly to Finance.

------------------------------------------------------------------------

## Features

### Staff

-   Submit expenses using:
    -   Receipt image
    -   Pasted receipt text
    -   Manual entry
-   AI extracts:
    -   Merchant
    -   Amount
    -   Expense date
    -   Category
    -   Reason
-   Review and correct extracted details before submission.
-   Receipt-derived expense date is read-only.
-   Receipt workflow is blocked when an expense date cannot be reliably
    extracted.
-   View claim history and current status.
-   See rejection reasons.
-   Duplicate claims are detected before submission.

### Manager

-   View pending claims from their team.
-   Approve or reject team claims.
-   Rejection requires a reason.
-   Submit personal expense claims.
-   Manager's own claims cannot be approved by the same manager and go
    directly to Finance.

### Finance

-   View claims pending Finance approval.
-   Approve and reimburse claims using a simulated bank transfer.
-   Reject claims with a required reason.
-   View monthly actual approved/reimbursed spending.
-   Analyze spending by:
    -   Employee
    -   Category
    -   Employee × Category
    -   Day
-   View rejected claim statistics and rejection reasons.
-   Monitor Staff and Manager spending against their monthly limits.

> Monthly limits are used for monitoring and visual alerts only. Claims
> are not automatically blocked when a limit is reached.

------------------------------------------------------------------------

## Workflow

``` text
Staff
  │
  ├── Upload receipt / Paste receipt / Manual entry
  │
  ├── AI extraction
  │
  ├── Review and correction
  │
  ├── Duplicate detection
  │
  ▼
PENDING_MANAGER
  │
  ├── Manager approves ──────────────┐
  │                                  ▼
  └── Manager rejects          PENDING_FINANCE
                                      │
                                      ├── Finance approves
                                      │        │
                                      │        ▼
                                      │    REIMBURSED
                                      │
                                      └── Finance rejects
                                               │
                                               ▼
                                      REJECTED_BY_FINANCE
```

Manager self-claims follow:

``` text
Manager submits claim
        │
        ▼
PENDING_FINANCE
        │
        ▼
Finance review
```

A reimbursed claim is final and cannot move backwards.

------------------------------------------------------------------------

## Tech Stack

-   **Python**
-   **Streamlit** --- user interface
-   **Supabase / PostgreSQL** --- database
-   **Groq API** --- receipt text/image extraction
-   **Qwen model** --- structured receipt extraction
-   **RapidFuzz** --- fuzzy duplicate detection
-   **Pandas / Streamlit charts** --- analytics and visualization

------------------------------------------------------------------------

## Project Structure

``` text
expense_claims/
│
├── app.py
├── supabase_client.py
├── claims.py
├── ai_extractor.py
├── duplicate_detector.py
├── analytics.py
│
├── receipts/
│
├── requirements.txt
├── .env
└── .gitignore
```

### Module responsibilities

  -----------------------------------------------------------------------
  File                                Responsibility
  ----------------------------------- -----------------------------------
  `app.py`                            Streamlit UI and role-based
                                      workflows

  `claims.py`                         Claim creation, approval, rejection
                                      and reimbursement logic

  `ai_extractor.py`                   Receipt text/image extraction using
                                      Groq

  `duplicate_detector.py`             Fuzzy duplicate detection

  `analytics.py`                      Finance reporting and monthly
                                      spending analysis

  `supabase_client.py`                Supabase connection
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## Database Design

The application uses two main tables:

### `employees`

Stores:

-   Employee ID
-   Name
-   Email
-   Role
-   Manager relationship
-   Monthly spending limit

Example roles:

``` text
staff
manager
finance
```

### `claims`

Stores:

-   Claim ID
-   Employee
-   Amount
-   Expense date
-   Claim submission timestamp
-   Merchant
-   Category
-   Reason
-   Receipt text/path
-   Claim status
-   Manager approval information
-   Finance approval information
-   Reimbursement/payment information
-   Rejection information
-   Duplicate information

Claim IDs use a human-readable format such as:

``` text
VSP-CLM-001
```

Employee IDs use:

``` text
VSP-STF-01
VSP-STF-02
VSP-STF-03
VSP-MGR-01
VSP-FIN-01
```

------------------------------------------------------------------------

## Claim Statuses

``` text
PENDING_MANAGER
APPROVED_BY_MANAGER
PENDING_FINANCE
REJECTED_BY_MANAGER
APPROVED_BY_FINANCE
REJECTED_BY_FINANCE
REIMBURSED
```

The application treats `REIMBURSED` as the final successful state.

------------------------------------------------------------------------

## Duplicate Detection

Duplicate detection is designed for a realistic problem: the same
receipt may be submitted again with slightly different wording.

The system compares claims belonging to the same employee using:

-   Expense date
-   Amount
-   Merchant similarity
-   Reason similarity

### Same date

A claim is blocked when:

-   Same employee
-   Same expense date
-   Same amount
-   Merchant similarity ≥ 80%
-   Reason similarity ≥ 60%

Result:

``` text
BLOCK_DUPLICATE
```

### Different date

If the same criteria match but the expense date is different, the claim
is allowed but flagged:

``` text
POSSIBLE_DUPLICATE
```

This allows legitimate recurring expenses while still alerting
reviewers.

------------------------------------------------------------------------

## AI Receipt Extraction

Users can paste receipt text or upload a receipt image.

The AI converts unstructured receipt information into structured fields:

``` json
{
  "merchant": "...",
  "amount": 800,
  "expense_date": "2026-09-18",
  "category": "Travel",
  "reason": "..."
}
```

The extracted information is shown to the employee before submission so
that incorrect extraction can be corrected.

The application does not intentionally invent missing receipt
information. The expense date is treated as a required field for the
receipt-based workflow.

------------------------------------------------------------------------

## Finance Analytics

The Finance dashboard provides:

-   Total actual expense
-   Number of approved/reimbursed claims
-   Expense by employee
-   Expense by category
-   Employee × category spending
-   Daily expense trend
-   Rejected claim count
-   Rejected amount
-   Rejection rate
-   Rejection reasons
-   Monthly spending vs employee limit

Actual expense is calculated from claims that have reached:

``` text
APPROVED_BY_FINANCE
REIMBURSED
```

Rejected claims are reported separately.

------------------------------------------------------------------------

## Monthly Limit Monitoring

Staff and Manager monthly limits are stored in the employee record.

Finance can see:

-   Amount spent
-   Monthly limit
-   Remaining amount
-   Utilization percentage

Visual thresholds:

``` text
< 80%       Normal
80–99.9%    Near limit warning
≥ 100%      Limit exceeded
```

The limit is a monitoring mechanism rather than an enforcement rule
because the business requirement specifies that Finance needs visibility
into employees who have gone over their limit, but does not define a
mandatory claim-blocking amount or policy.

------------------------------------------------------------------------

## Setup

### 1. Clone the repository

``` bash
git clone <your-github-repository-url>
cd expense_claims
```

### 2. Create a virtual environment

``` bash
python -m venv venv
```

Windows:

``` bash
venv\Scripts\activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file:

``` env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
GROQ_API_KEY=your_groq_api_key
```

Do not commit `.env` to GitHub.

### 5. Configure Supabase

Create the `employees` and `claims` tables using the SQL schema used by
the application.

The database should contain realistic sample employees and claims
covering:

-   Normal claims
-   Rejected claims
-   Reimbursed claims
-   Duplicate/possible duplicate claims
-   A manager's own claim
-   An employee close to the monthly spending limit

### 6. Run the application

``` bash
streamlit run app.py
```

The application will open in the browser.

------------------------------------------------------------------------

## Security Notes

-   API keys are stored in environment variables.
-   `.env` should never be committed.
-   The application uses the Supabase client rather than exposing
    database credentials in the UI.
-   Payment is intentionally simulated because a real payment gateway is
    not required for this assignment.

------------------------------------------------------------------------

## Design Decisions & Assumptions

### 1. No authentication system

For this take-home application, role selection is used to demonstrate
the Staff, Manager, and Finance workflows without introducing
unnecessary authentication infrastructure.

### 2. One employees table

All employees are stored in a single table with a `role` field and
manager relationship. This avoids duplicating employee data across
role-specific tables.

### 3. Human-readable IDs

Human-readable IDs make the application easier to demonstrate and debug:

``` text
VSP-STF-01
VSP-MGR-01
VSP-FIN-01
VSP-CLM-001
```

### 4. Expense date vs claim date

`expense_date` represents when the expense happened.

`claim_date` represents when the employee submitted the claim.

This distinction is important for month-end reporting and late
submissions.

### 5. Calculated totals

Total spending is calculated from claims rather than stored as a
separate total. This avoids maintaining duplicate aggregate data.

### 6. Duplicate handling

A different expense date can represent a legitimate recurring expense,
so matching claims on different dates are flagged rather than
automatically blocked.

### 7. Simulated payment

Finance reimbursement uses a simulated bank transfer and generates a
payment identifier. No real money is moved.

### 8. Monthly limits

Limits are monitored and highlighted on the Finance dashboard. They are
not used to automatically prevent submission.

### 9. Receipt date validation

The receipt workflow requires an extracted expense date. Employees can
use Manual Entry when a receipt is unavailable.

------------------------------------------------------------------------

## AI Tools Used

### Groq + Qwen

Used in `ai_extractor.py` for:

-   Receipt text extraction
-   Receipt image extraction
-   Converting unstructured receipt information into structured claim
    fields

### ChatGPT

Used during development for:

-   Architecture discussion
-   SQL/database design
-   Debugging
-   Code review
-   Test-case design
-   README/documentation preparation

The final application logic was reviewed and integrated into the project
code.

------------------------------------------------------------------------

## Test Scenarios

The application was designed around realistic cases including:

1.  Normal Staff claim
2.  Staff claim with receipt image
3.  Staff claim using pasted receipt text
4.  Manual claim
5.  Missing receipt date
6.  Same receipt submitted twice on the same date
7.  Same receipt submitted later with different wording
8.  Manager submitting a personal claim
9.  Manager approving a team claim
10. Manager rejecting a team claim
11. Finance reimbursing a claim
12. Finance rejecting a claim
13. Employee approaching monthly spending limit
14. Employee exceeding monthly spending limit
15. Monthly Finance analytics

------------------------------------------------------------------------

## What I Would Build Next With Another Week

If the project had another week of development time, I would focus on:

### 1. Authentication and authorization

Replace role selection with real user authentication and enforce
permissions at the application/database level.

### 2. Better audit trail

Create an immutable claim-event history recording:

-   Who performed an action
-   What changed
-   When it changed
-   Previous status
-   New status

### 3. Production receipt storage

Move receipt files from the local filesystem to Supabase Storage or
another object-storage service.

### 4. Stronger duplicate detection

Combine fuzzy matching with receipt image fingerprints, merchant
normalization, transaction references and configurable confidence
thresholds.

### 5. Finance reporting improvements

Add exportable monthly reports and configurable reporting periods.

### 6. Automated notifications

Notify employees when claims are:

-   Approved
-   Rejected
-   Reimbursed
-   Waiting for action

### 7. Production deployment

Deploy the Streamlit application with managed secrets and production
database policies.

------------------------------------------------------------------------

## Demo Data

The project uses fictional employees and realistic sample expenses so
that the complete workflow can be demonstrated without exposing real
employee or financial information.

------------------------------------------------------------------------

## License

This project is created as a take-home assignment demonstration.
