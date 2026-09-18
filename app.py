import streamlit as st
from datetime import date
import calendar
import os
import uuid
from claims import (
    create_claim,
    get_employee_claims,
    get_manager_pending_claims,
    approve_claim_by_manager,
    reject_claim_by_manager,
    get_finance_pending_claims,
    approve_and_reimburse_claim,
    reject_claim_by_finance,
)
from analytics import (
    get_total_expense,
    get_total_claims,
    get_expense_by_employee,
    get_expense_by_category,
    get_employee_category_expense,
    get_rejection_summary,
    get_rejected_claims,
    get_daily_expense,
    get_employee_monthly_spending_with_limit
)

from ai_extractor import (
    extract_from_text,
    extract_from_image
)

from duplicate_detector import check_duplicate



# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Expense Claims",
    page_icon="💰",
    layout="wide"
)


# ==================================================
# ROLE SELECTION
# ==================================================

st.title("Expense Claims")

role = st.sidebar.selectbox(
    "Select Role",
    ["Staff", "Manager", "Finance"]
)


# ==================================================
# STAFF DASHBOARD
# ==================================================

if role == "Staff":

    st.header("Staff Dashboard")

    # ------------------------------------------------
    # STAFF SELECTION
    # ------------------------------------------------

    staff_id = st.sidebar.selectbox(
        "Staff",
        [
            "VSP-STF-01",
            "VSP-STF-02",
            "VSP-STF-03"
        ]
    )

    st.divider()

    # ------------------------------------------------
    # STAFF TABS
    # ------------------------------------------------

    submit_tab, history_tab = st.tabs(
        ["Submit Expense", "My Claims"]
    )

    # =================================================
    # SUBMIT EXPENSE
    # =================================================

    with submit_tab:

        st.subheader("Submit Expense")

        input_method = st.radio(
            "Receipt input",
            [
                "Upload Receipt",
                "Paste Receipt Text",
                "Manual Entry"
            ],
            horizontal=True
        )

        extracted_data = None
        receipt_text = None
        receipt_path = None

        # ---------------------------------------------
        # UPLOAD RECEIPT
        # ---------------------------------------------

        if input_method == "Upload Receipt":

            uploaded_file = st.file_uploader(
                "Upload receipt",
                type=["jpg", "jpeg", "png"],
                help="Upload a clear receipt image."
            )

            if uploaded_file:

                st.image(
                    uploaded_file,
                    caption="Uploaded Receipt",
                    width=450
                )

                os.makedirs(
                    "receipts",
                    exist_ok=True
                )

                file_name = (
                    f"{uuid.uuid4()}_"
                    f"{uploaded_file.name}"
                )

                receipt_path = os.path.join(
                    "receipts",
                    file_name
                )

                with open(
                    receipt_path,
                    "wb"
                ) as file:
                    file.write(
                        uploaded_file.getbuffer()
                    )

                if st.button(
                    "Extract Receipt Details",
                    type="primary"
                ):

                    with st.spinner(
                        "AI is reading the receipt..."
                    ):

                        try:
                            extracted_data = (
                                extract_from_image(
                                    receipt_path
                                )
                            )

                            st.session_state[
                                "extracted_data"
                            ] = extracted_data

                            st.session_state[
                                "receipt_path"
                            ] = receipt_path

                            st.success(
                                "Receipt details extracted."
                            )

                        except Exception as e:

                            st.error(
                                f"Extraction failed: {e}"
                            )

        # ---------------------------------------------
        # PASTE RECEIPT TEXT
        # ---------------------------------------------

        elif input_method == "Paste Receipt Text":

            receipt_text = st.text_area(
                "Paste receipt text",
                height=200,
                placeholder=(
                    "Example:\n"
                    "Uber India\n"
                    "Trip to client office\n"
                    "Date: 18/09/2026\n"
                    "Total: ₹800"
                )
            )

            if st.button(
                "Extract Receipt Details",
                type="primary"
            ):

                if not receipt_text.strip():

                    st.warning(
                        "Please paste the receipt text."
                    )

                else:

                    with st.spinner(
                        "AI is extracting the receipt..."
                    ):

                        try:

                            extracted_data = (
                                extract_from_text(
                                    receipt_text
                                )
                            )

                            st.session_state[
                                "extracted_data"
                            ] = extracted_data

                            st.success(
                                "Receipt details extracted."
                            )

                        except Exception as e:

                            st.error(
                                f"Extraction failed: {e}"
                            )

        # ---------------------------------------------
        # MANUAL ENTRY
        # ---------------------------------------------

        elif input_method == "Manual Entry":

            st.info(
                "Manual entry is available when "
                "no receipt is available."
            )

            merchant = st.text_input(
                "Merchant"
            )

            amount = st.number_input(
                "Amount",
                min_value=0.01,
                step=10.0
            )

            expense_date = st.date_input(
                "Expense Date",
                value=date.today()
            )

            category = st.selectbox(
                "Category",
                [
                    "Travel",
                    "Meals",
                    "Supplies",
                    "Accommodation",
                    "Communication",
                    "Other"
                ]
            )

            reason = st.text_area(
                "Reason"
            )

            if st.button(
                "Prepare Claim",
                type="primary"
            ):

                if not merchant or not reason:

                    st.warning(
                        "Merchant and reason are required."
                    )

                else:

                    st.session_state[
                        "extracted_data"
                    ] = {
                        "merchant": merchant,
                        "amount": amount,
                        "expense_date": str(
                            expense_date
                        ),
                        "category": category,
                        "reason": reason
                    }

                    st.session_state[
                        "receipt_text"
                    ] = None

                    st.success(
                        "Claim prepared for review."
                    )

        # =================================================
        # REVIEW EXTRACTED DETAILS
        # =================================================

        if "extracted_data" in st.session_state:

            data = st.session_state[
                "extracted_data"
            ]

            st.divider()

            st.subheader(
                "Review Extracted Details"
            )

            st.caption(
                "Verify the extracted information before submission."
            )

            merchant = st.text_input(
                "Merchant",
                value=data.get("merchant") or ""
            )

            amount = st.number_input(
                "Amount",
                min_value=0.01,
                value=float(
                    data.get("amount") or 0.01
                ),
                step=10.0
            )

            # ---------------------------------------------
            # EXPENSE DATE — READ ONLY
            # ---------------------------------------------

            extracted_date = data.get(
                "expense_date"
            )

            st.text_input(
                "Expense Date",
                value=(
                    extracted_date
                    if extracted_date
                    else "Date not detected"
                ),
                disabled=True
            )

            expense_date = extracted_date

            category = st.selectbox(
                "Category",
                [
                    "Travel",
                    "Meals",
                    "Supplies",
                    "Accommodation",
                    "Communication",
                    "Other"
                ],
                key="manual_category",
                index=(
                    [
                        "Travel",
                        "Meals",
                        "Supplies",
                        "Accommodation",
                        "Communication",
                        "Other"
                    ].index(
                        data.get("category")
                    )
                    if data.get("category")
                    in [
                        "Travel",
                        "Meals",
                        "Supplies",
                        "Accommodation",
                        "Communication",
                        "Other"
                    ]
                    else 5
                )
            )

            reason = st.text_area(
                "Reason",
                value=data.get("reason") or ""
            )

            # ---------------------------------------------
            # DATE VALIDATION
            # ---------------------------------------------

            if not expense_date:

                st.error(
                    "Expense date could not be reliably "
                    "extracted. This claim cannot be submitted "
                    "through the receipt workflow."
                )

            else:

                # -----------------------------------------
                # DUPLICATE CHECK
                # -----------------------------------------

                if st.button(
                    "Check & Submit Claim",
                    type="primary"
                ):

                    duplicates = check_duplicate(
                        employee_id=staff_id,
                        amount=amount,
                        expense_date=expense_date,
                        merchant=merchant,
                        reason=reason
                    )

                    blocked = [
                        d for d in duplicates
                        if d["classification"]
                        == "BLOCK_DUPLICATE"
                    ]

                    possible = [
                        d for d in duplicates
                        if d["classification"]
                        == "POSSIBLE_DUPLICATE"
                    ]

                    # -------------------------------------
                    # BLOCK DUPLICATE
                    # -------------------------------------

                    if blocked:

                        st.error(
                            "🚫 Duplicate claim detected. "
                            "Submission blocked."
                        )

                        for duplicate in blocked:

                            st.write(
                                f"**Existing Claim:** "
                                f"{duplicate['claim_id']}"
                            )

                            st.write(
                                f"Merchant similarity: "
                                f"{duplicate['merchant_score']:.1f}%"
                            )

                            st.write(
                                f"Reason similarity: "
                                f"{duplicate['reason_score']:.1f}%"
                            )

                            st.write(
                                f"Existing status: "
                                f"{duplicate['status']}"
                            )

                    else:

                        # ---------------------------------
                        # POSSIBLE DUPLICATE WARNING
                        # ---------------------------------

                        if possible:

                            st.warning(
                                "⚠️ Possible similar claim detected."
                            )

                            for duplicate in possible:

                                similarity = (
                                    duplicate[
                                        "merchant_score"
                                    ]
                                    + duplicate[
                                        "reason_score"
                                    ]
                                ) / 2

                                st.write(
                                    f"**Related Claim:** "
                                    f"{duplicate['claim_id']}"
                                )

                                st.write(
                                    f"Similarity: "
                                    f"{similarity:.1f}%"
                                )

                                st.write(
                                    "Same merchant/amount "
                                    "but different expense date. "
                                    "Claim is allowed but flagged "
                                    "for reviewer attention."
                                )

                        # ---------------------------------
                        # CREATE CLAIM
                        # ---------------------------------

                        try:

                            result = create_claim(
                                employee_id=staff_id,
                                amount=amount,
                                expense_date=expense_date,
                                merchant=merchant,
                                category=category,
                                reason=reason,
                                receipt_text=(
                                    receipt_text
                                    or st.session_state.get(
                                        "receipt_text"
                                    )
                                ),
                                receipt_url=(
                                    st.session_state.get(
                                        "receipt_path"
                                    )
                                )
                            )

                            if result["success"]:

                                st.success(
                                    "✅ Claim submitted successfully."
                                )

                                claim = result[
                                    "claim"
                                ][0]

                                st.info(
                                    f"Claim ID: "
                                    f"**{claim['claim_id']}**"
                                )

                                if possible:

                                    st.warning(
                                        "This claim has been "
                                        "flagged as a possible "
                                        "duplicate for reviewers."
                                    )

                                st.session_state.pop(
                                    "extracted_data",
                                    None
                                )

                            else:

                                st.error(
                                    result["message"]
                                )

                        except Exception as e:

                            st.error(
                                f"Claim submission failed: {e}"
                            )


    # =================================================
    # MY CLAIMS
    # =================================================

    with history_tab:

        st.subheader("My Claims")

        claims = get_employee_claims(
            staff_id
        )

        if claims:

            for claim in claims:

                with st.expander(
                    f"{claim['claim_id']} — "
                    f"₹{float(claim['amount']):,.2f}"
                ):

                    st.write(
                        f"**Merchant:** "
                        f"{claim['merchant']}"
                    )

                    st.write(
                        f"**Category:** "
                        f"{claim['category']}"
                    )

                    st.write(
                        f"**Expense Date:** "
                        f"{claim['expense_date']}"
                    )

                    st.write(
                        f"**Reason:** "
                        f"{claim['reason']}"
                    )

                    st.write(
                        f"**Status:** "
                        f"{claim['status']}"
                    )


                    if claim.get(
                        "rejection_reason"
                    ):

                        st.error(
                            f"Rejection reason: "
                            f"{claim['rejection_reason']}"
                        )

                    if claim.get(
                        "duplicate_flag"
                    ):

                        st.warning(
                            "⚠️ This claim was flagged "
                            "as a possible duplicate."
                        )

        else:

            st.info(
                "You have no claims yet."
            )




# ==================================================
# MANAGER DASHBOARD
# ==================================================

elif role == "Manager":

    st.header("Manager Dashboard")

    manager_id = "VSP-MGR-01"

    team_tab, submit_tab, my_claims_tab = st.tabs(
        ["Team Claims", "Submit Expense", "My Claims"]
    )

    # =================================================
    # TEAM CLAIMS
    # =================================================

    with team_tab:

        st.subheader("Pending Team Claims")

        pending_claims = get_manager_pending_claims(
            manager_id
        )

        if not pending_claims:

            st.success(
                "No claims are currently pending approval."
            )

        else:

            for claim in pending_claims:

                with st.container(border=True):

                    st.markdown(
                        f"### {claim['claim_id']}"
                    )

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.write(
                            f"**Employee**\n"
                            f"{claim['employee_id']}"
                        )

                    with col2:
                        st.write(
                            f"**Amount**\n"
                            f"₹{float(claim['amount']):,.2f}"
                        )

                    with col3:
                        st.write(
                            f"**Expense Date**\n"
                            f"{claim['expense_date']}"
                        )

                    with col4:
                        st.write(
                            f"**Category**\n"
                            f"{claim['category']}"
                        )

                    st.write(
                        f"**Merchant:** "
                        f"{claim['merchant']}"
                    )

                    st.write(
                        f"**Reason:** "
                        f"{claim['reason']}"
                    )

                    # ---------------------------------
                    # POSSIBLE DUPLICATE
                    # ---------------------------------

                    if claim.get("duplicate_flag"):

                        st.warning(
                            "⚠️ Possible duplicate claim"
                        )

                        if claim.get(
                            "duplicate_of_claim_id"
                        ):

                            st.write(
                                f"Related claim: "
                                f"**{claim['duplicate_of_claim_id']}**"
                            )

                        st.caption(
                            "This claim was flagged by the "
                            "duplicate detection system and "
                            "requires reviewer attention."
                        )

                    # ---------------------------------
                    # RECEIPT
                    # ---------------------------------

                    if claim.get("receipt_url"):

                        receipt_path = (
                            claim["receipt_url"]
                        )

                        if os.path.exists(
                            receipt_path
                        ):

                            st.image(
                                receipt_path,
                                caption="Receipt",
                                width=400
                            )

                    # ---------------------------------
                    # ACTIONS
                    # ---------------------------------

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Approve",
                            key=f"approve_{claim['claim_id']}",
                            type="primary"
                        ):

                            try:

                                approve_claim_by_manager(
                                    claim["claim_id"],
                                    manager_id
                                )

                                st.success(
                                    f"{claim['claim_id']} "
                                    "approved."
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(str(e))

                    with col2:

                        reject_reason = st.text_input(
                            "Rejection reason",
                            key=f"reason_{claim['claim_id']}",
                            placeholder=(
                                "Enter reason before rejecting"
                            )
                        )

                        if st.button(
                            "Reject",
                            key=f"reject_{claim['claim_id']}"
                        ):

                            if not reject_reason.strip():

                                st.warning(
                                    "A rejection reason is required."
                                )

                            else:

                                try:

                                    reject_claim_by_manager(
                                        claim["claim_id"],
                                        manager_id,
                                        reject_reason
                                    )

                                    st.success(
                                        f"{claim['claim_id']} "
                                        "rejected."
                                    )

                                    st.rerun()

                                except Exception as e:

                                    st.error(str(e))

    # =================================================
    # MANAGER SUBMIT EXPENSE
    # =================================================

    with submit_tab:

        st.subheader("Submit Expense")

        manager_input_method = st.radio(
            "Input Method",
            ["Upload Receipt", "Paste Receipt Text", "Manual Entry"],
            horizontal=True,
            key="manager_input_method"
        )

        manager_extracted_data = None
        manager_receipt_path = None
        manager_receipt_text = None

        # ---------------------------------------------
        # UPLOAD RECEIPT
        # ---------------------------------------------

        if manager_input_method == "Upload Receipt":

            uploaded_file = st.file_uploader(
                "Upload receipt",
                type=["jpg", "jpeg", "png"],
                key="manager_receipt_upload"
            )

            if uploaded_file:

                os.makedirs("receipts", exist_ok=True)

                manager_receipt_path = os.path.join(
                    "receipts",
                    uploaded_file.name
                )

                with open(manager_receipt_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.image(
                    uploaded_file,
                    caption="Uploaded Receipt",
                    width=400
                )

                if st.button(
                    "Extract Receipt Details",
                    key="manager_extract_image"
                ):
                    try:
                        extracted = extract_from_image(
                            manager_receipt_path
                        )

                        st.session_state[
                            "manager_extracted_data"
                        ] = extracted

                        st.session_state[
                            "manager_receipt_path"
                        ] = manager_receipt_path

                        st.success(
                            "Receipt details extracted successfully."
                        )

                    except Exception as e:
                        st.error(
                            f"Extraction failed: {str(e)}"
                        )

        # ---------------------------------------------
        # PASTE RECEIPT TEXT
        # ---------------------------------------------

        elif manager_input_method == "Paste Receipt Text":

            manager_receipt_text = st.text_area(
                "Paste receipt text",
                height=180,
                key="manager_receipt_text"
            )

            if st.button(
                "Extract Receipt Details",
                key="manager_extract_text"
            ):

                if not manager_receipt_text.strip():

                    st.warning(
                        "Please paste receipt text first."
                    )

                else:

                    try:
                        extracted = extract_from_text(
                            manager_receipt_text
                        )

                        st.session_state[
                            "manager_extracted_data"
                        ] = extracted

                        st.session_state[
                            "manager_receipt_text_value"
                        ] = manager_receipt_text

                        st.success(
                            "Receipt details extracted successfully."
                        )

                    except Exception as e:
                        st.error(
                            f"Extraction failed: {str(e)}"
                        )

        # ---------------------------------------------
        # MANUAL ENTRY
        # ---------------------------------------------

        else:

            merchant = st.text_input(
                "Merchant",
                key="manager_manual_merchant"
            )

            amount = st.number_input(
                "Amount",
                min_value=0.01,
                step=10.0,
                key="manager_manual_amount"
            )

            expense_date = st.date_input(
                "Expense Date",
                key="manager_manual_date"
            )

            category = st.selectbox(
                "Category",
                [
                    "Travel",
                    "Meals",
                    "Supplies",
                    "Accommodation",
                    "Communication",
                    "Other"
                ],
                key="manager_manual_category"
            )

            reason = st.text_area(
                "Reason",
                key="manager_manual_reason"
            )

            if st.button(
                "Prepare Claim",
                key="manager_prepare_manual"
            ):

                st.session_state[
                    "manager_extracted_data"
                ] = {
                    "merchant": merchant,
                    "amount": amount,
                    "expense_date": str(expense_date),
                    "category": category,
                    "reason": reason
                }

        # ---------------------------------------------
        # REVIEW EXTRACTED DETAILS
        # ---------------------------------------------

        if "manager_extracted_data" in st.session_state:

            data = st.session_state[
                "manager_extracted_data"
            ]

            st.divider()

            st.subheader("Review Claim Details")

            review_merchant = st.text_input(
                "Merchant",
                value=str(data.get("merchant", "")),
                key="manager_review_merchant"
            )

            review_amount = st.number_input(
                "Amount",
                min_value=0.01,
                value=float(data.get("amount", 0)),
                step=10.0,
                key="manager_review_amount"
            )

            # Receipt-derived date is read-only
            if manager_input_method != "Manual Entry":

                review_date = data.get("expense_date")

                st.text_input(
                    "Expense Date",
                    value=str(review_date),
                    disabled=True,
                    key="manager_review_date_readonly"
                )

            else:

                review_date = data.get("expense_date")

                st.text_input(
                    "Expense Date",
                    value=str(review_date),
                    disabled=True,
                    key="manager_review_manual_date"
                )

            review_category = st.selectbox(
                "Category",
                [
                    "Travel",
                    "Meals",
                    "Supplies",
                    "Accommodation",
                    "Communication",
                    "Other"
                ],
                index=[
                    "Travel",
                    "Meals",
                    "Supplies",
                    "Accommodation",
                    "Communication",
                    "Other"
                ].index(
                    data.get("category", "Other")
                ),
                key="manager_review_category"
            )

            review_reason = st.text_area(
                "Reason",
                value=str(data.get("reason", "")),
                key="manager_review_reason"
            )

            # -----------------------------------------
            # SUBMIT
            # -----------------------------------------

            if st.button(
                "Submit Claim",
                type="primary",
                key="manager_submit_claim"
            ):

                if not review_merchant.strip():
                    st.error("Merchant is required.")

                elif review_amount <= 0:
                    st.error("Amount must be greater than zero.")

                elif not review_reason.strip():
                    st.error("Reason is required.")

                elif not review_date:
                    st.error(
                        "Receipt expense date is required."
                    )

                else:

                    try:

                        result = create_claim(
                            employee_id=manager_id,
                            amount=review_amount,
                            expense_date=str(review_date),
                            merchant=review_merchant,
                            category=review_category,
                            reason=review_reason,
                            receipt_text=st.session_state.get(
                                "manager_receipt_text_value"
                            ),
                            receipt_url=st.session_state.get(
                                "manager_receipt_path"
                            )
                        )

                        if not result["success"]:

                            st.error(
                                result["message"]
                            )

                            if result.get("duplicates"):
                                st.warning(
                                    "Existing duplicate claim(s) detected."
                                )

                        else:

                            if result.get(
                                "possible_duplicates"
                            ):

                                st.warning(
                                    "Claim submitted, but a "
                                    "possible duplicate was detected."
                                )

                            else:

                                st.success(
                                    f"{result['claim'][0]['claim_id']} "
                                    "submitted successfully."
                                )

                            st.info(
                                "As a manager, your claim goes "
                                "directly to Finance for processing."
                            )

                            # Clear manager extraction state
                            for key in [
                                "manager_extracted_data",
                                "manager_receipt_path",
                                "manager_receipt_text_value"
                            ]:
                                st.session_state.pop(
                                    key,
                                    None
                                )

                    except Exception as e:

                        st.error(
                            f"Claim submission failed: {str(e)}"
                        )
    
    
    # =================================================
    # MANAGER'S OWN CLAIMS
    # =================================================

    with my_claims_tab:

        st.subheader("My Claims")

        manager_claims = get_employee_claims(
            manager_id
        )

        if manager_claims:

            for claim in manager_claims:

                with st.expander(
                    f"{claim['claim_id']} — "
                    f"₹{float(claim['amount']):,.2f}"
                ):

                    st.write(
                        f"**Merchant:** "
                        f"{claim['merchant']}"
                    )

                    st.write(
                        f"**Category:** "
                        f"{claim['category']}"
                    )

                    st.write(
                        f"**Expense Date:** "
                        f"{claim['expense_date']}"
                    )

                    st.write(
                        f"**Reason:** "
                        f"{claim['reason']}"
                    )

                    st.write(
                        f"**Status:** "
                        f"{claim['status']}"
                    )

                    if claim.get(
                        "rejection_reason"
                    ):

                        st.error(
                            f"Rejection reason: "
                            f"{claim['rejection_reason']}"
                        )


        else:

            st.info(
                "You have no claims."
            )
# ==================================================
# FINANCE DASHBOARD
# ==================================================

elif role == "Finance":

    st.header("Finance Dashboard")

    st.caption(
        "Actual approved/reimbursed expenses"
    )

    # =================================================
    # PENDING FINANCE CLAIMS
    # =================================================

    st.subheader("Pending Finance Claims")

    finance_id = "VSP-FIN-01"

    pending_finance_claims = get_finance_pending_claims()


    if not pending_finance_claims:

        st.success(
            "No claims are currently pending Finance approval."
        )

    else:

        for claim in pending_finance_claims:
            

            with st.container(border=True):

                st.markdown(
                    f"### {claim['claim_id']}"
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.write(
                        f"**Employee**\n"
                        f"{claim['employee_id']}"
                    )

                with col2:
                    st.write(
                        f"**Amount**\n"
                        f"₹{float(claim['amount']):,.2f}"
                    )

                with col3:
                    st.write(
                        f"**Expense Date**\n"
                        f"{claim['expense_date']}"
                    )

                with col4:
                    st.write(
                        f"**Category**\n"
                        f"{claim['category']}"
                    )

                st.write(
                    f"**Merchant:** {claim['merchant']}"
                )

                st.write(
                    f"**Reason:** {claim['reason']}"
                )

                # -----------------------------------------
                # DUPLICATE WARNING
                # -----------------------------------------

                if claim.get("duplicate_flag"):

                    st.warning(
                        "⚠️ Possible duplicate claim"
                    )

                    if claim.get("duplicate_of_claim_id"):

                        st.write(
                            f"Related claim: "
                            f"**{claim['duplicate_of_claim_id']}**"
                        )

                    st.caption(
                        "Review the related claim before "
                        "processing reimbursement."
                    )

                # -----------------------------------------
                # RECEIPT
                # -----------------------------------------

                if claim.get("receipt_url"):

                    receipt_path = claim["receipt_url"]

                    if os.path.exists(receipt_path):

                        st.image(
                            receipt_path,
                            caption="Receipt",
                            width=400
                        )

        

                # -----------------------------------------
                # FINANCE ACTIONS
                # -----------------------------------------

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "Approve & Reimburse",
                        key=f"finance_approve_{claim['claim_id']}",
                        type="primary"
                    ):

                        try:

                            approve_and_reimburse_claim(
                                claim["claim_id"],
                                finance_id
                            )

                            st.success(
                                f"{claim['claim_id']} "
                                "approved and reimbursed."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(str(e))

                with col2:

                    finance_reject_reason = st.text_input(
                        "Rejection reason",
                        key=f"finance_reason_{claim['claim_id']}",
                        placeholder=(
                            "Enter reason before rejecting"
                        )
                    )

                    if st.button(
                        "Reject",
                        key=f"finance_reject_{claim['claim_id']}"
                    ):

                        if not finance_reject_reason.strip():

                            st.warning(
                                "A rejection reason is required."
                            )

                        else:

                            try:

                                reject_claim_by_finance(
                                    claim["claim_id"],
                                    finance_id,
                                    finance_reject_reason
                                )

                                st.success(
                                    f"{claim['claim_id']} "
                                    "rejected."
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(str(e))

    st.divider()

    # ------------------------------------------------
    # MONTH SELECTOR
    # ------------------------------------------------

    selected_month = st.selectbox(
        "Month",
        range(1, 13),
        index=date.today().month - 1,
        format_func=lambda month:
            calendar.month_name[month]
    )

    selected_year = date.today().year

    start_date = (
        f"{selected_year}-"
        f"{selected_month:02d}-01"
    )

    last_day = calendar.monthrange(
        selected_year,
        selected_month
    )[1]

    end_date = (
        f"{selected_year}-"
        f"{selected_month:02d}-"
        f"{last_day:02d}"
    )

    # =================================================
    # EMPLOYEE MONTHLY LIMIT MONITORING
    # =================================================

    st.subheader("Employee Monthly Spending vs Limit")

    limit_data = get_employee_monthly_spending_with_limit(
        start_date,
        end_date
    )

    if not limit_data:
        st.info("No Staff or Manager spending data available.")
    else:
        for employee in limit_data:

            spending = employee["spending"]
            monthly_limit = employee["monthly_limit"]
            utilization = employee["utilization"]
            remaining = employee["remaining"]

            st.markdown(f"### {employee['name']}")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Spent",
                    f"₹{spending:,.2f}"
                )

            with col2:
                st.metric(
                    "Monthly Limit",
                    f"₹{monthly_limit:,.2f}"
                )

            with col3:
                if remaining >= 0:
                    st.metric(
                        "Remaining",
                        f"₹{remaining:,.2f}"
                    )
                else:
                    st.metric(
                        "Exceeded By",
                        f"₹{abs(remaining):,.2f}"
                    )

            with col4:
                st.metric(
                    "Utilization",
                    f"{utilization:.1f}%"
                )

            # Visual threshold indicator
            if utilization >= 100:
                st.error(
                    f"🚨 Limit exceeded — {utilization:.1f}% of monthly limit used."
                )
            elif utilization >= 80:
                st.warning(
                    f"⚠️ Near monthly limit — {utilization:.1f}% used."
                )
            else:
                st.progress(
                    min(utilization / 100, 1.0),
                    text=f"{utilization:.1f}% of monthly limit used"
                )

            st.divider()

    # ------------------------------------------------
    # KPIs
    # ------------------------------------------------

    total_expense = get_total_expense(
        start_date,
        end_date
    )

    total_claims = get_total_claims(
        start_date,
        end_date
    )

    rejection_summary = get_rejection_summary(
        start_date,
        end_date
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Actual Expense",
            f"₹{total_expense:,.2f}"
        )

    with col2:
        st.metric(
            "Approved Claims",
            total_claims
        )

    with col3:
        st.metric(
            "Rejected Claims",
            rejection_summary[
                "rejected_count"
            ]
        )

    # ------------------------------------------------
    # EMPLOYEE EXPENSE
    # ------------------------------------------------

    st.divider()

    st.subheader(
        "Expense by Employee"
    )

    employee_expenses = get_expense_by_employee(
        start_date,
        end_date
    )

    if employee_expenses:

        st.bar_chart(
            {
                "Employee": list(
                    employee_expenses.keys()
                ),
                "Expense": list(
                    employee_expenses.values()
                )
            },
            x="Employee",
            y="Expense"
        )

    else:

        st.info(
            "No approved expenses for this month."
        )

    # ------------------------------------------------
    # CATEGORY EXPENSE
    # ------------------------------------------------

    st.subheader(
        "Expense by Category"
    )

    category_expenses = get_expense_by_category(
        start_date,
        end_date
    )

    if category_expenses:

        st.bar_chart(
            {
                "Category": list(
                    category_expenses.keys()
                ),
                "Expense": list(
                    category_expenses.values()
                )
            },
            x="Category",
            y="Expense"
        )

    else:

        st.info(
            "No approved expenses for this month."
        )

    # ------------------------------------------------
    # EMPLOYEE × CATEGORY
    # ------------------------------------------------

    st.divider()

    st.subheader(
        "Employee × Category Spending"
    )

    employee_category_data = (
        get_employee_category_expense(
            start_date,
            end_date
        )
    )

    if employee_category_data:

        st.dataframe(
            employee_category_data,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No approved expenses for this month."
        )

    # ------------------------------------------------
    # DAILY TREND
    # ------------------------------------------------

    st.subheader(
        "Daily Expense Trend"
    )

    daily_expense = get_daily_expense(
        start_date,
        end_date
    )

    if daily_expense:

        st.line_chart(
            {
                "Date": list(
                    daily_expense.keys()
                ),
                "Expense": list(
                    daily_expense.values()
                )
            },
            x="Date",
            y="Expense"
        )

    else:

        st.info(
            "No approved expenses for this month."
        )

    # ------------------------------------------------
    # REJECTED CLAIMS
    # ------------------------------------------------

    st.divider()

    st.subheader(
        "Rejected Claims"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Rejected Claims",
            rejection_summary[
                "rejected_count"
            ]
        )

    with col2:
        st.metric(
            "Rejected Amount",
            f"₹{rejection_summary['rejected_amount']:,.2f}"
        )

    with col3:
        st.metric(
            "Rejection Rate",
            f"{rejection_summary['rejection_rate']:.2f}%"
        )

    rejected_claims = get_rejected_claims(
        start_date,
        end_date
    )

    if rejected_claims:

        rejected_table = []

        for claim in rejected_claims:

            rejected_table.append({
                "Claim ID": claim["claim_id"],
                "Employee": claim["employee_id"],
                "Amount": (
                    f"₹{int(claim['amount']):,.0f}"
                ),
                "Category": claim["category"],
                "Status": claim["status"],
                "Reason": claim["rejection_reason"]
            })

        st.dataframe(
            rejected_table,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "No rejected claims for this month."
        )
