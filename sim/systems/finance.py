def finance_phase(world):
    for loan in world.loans.values():
        if loan.status != "active":
            continue

        interest = loan.remaining_balance * loan.interest_rate
        principal_due = loan.principal / loan.term_ticks
        payment_due = interest + principal_due

        borrower = world.companies.get(loan.borrower_id)
        bank = world.banks.get(loan.lender_id)

        if borrower and borrower.cash >= payment_due:
            borrower.cash -= payment_due
            loan.remaining_balance -= principal_due
            borrower.interest_paid_last_tick += interest
            borrower.principal_paid_last_tick += principal_due
            if bank:
                bank.reserves += payment_due
        elif borrower and borrower.cash >= interest:
            borrower.cash -= interest
            borrower.interest_paid_last_tick += interest
            if bank:
                bank.reserves += interest

        loan.ticks_elapsed += 1
        if loan.remaining_balance <= 0:
            loan.remaining_balance = 0.0
            loan.status = "paid_off"