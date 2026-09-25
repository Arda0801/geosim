"""
Government finance system: taxation, spending, bond issuance, debt interest.

Each function operates on the World and is called once per economic tick (week)
from World.run_tick().
"""


def collect_profit_tax(world):
    """
    Tax each company's profit_last_tick at the home nation's tax_rate.

    Only positive profits are taxed. Negative-cash companies are not penalized.
    This replaces the old cash-levy in World._nation_phase.
    """
    for nation in world.nations.values():
        nation.tax_collected_last_tick = 0.0
        for company in world.companies.values():
            if company.home_nation_id != nation.id:
                continue

            pre_tax_profit = (
                company.revenue_last_tick
                - company.input_costs_last_tick
                - company.wage_costs_last_tick
                - company.interest_paid_last_tick
                - company.principal_paid_last_tick
            )
            tax_due = max(0.0, pre_tax_profit * nation.tax_rate)
            tax = max(0.0, tax_due - company.tax_paid_last_tick)
            if tax <= 0:
                continue

            company.cash -= tax
            company.tax_paid_last_tick += tax
            company.profit_last_tick -= tax
            company.total_profit -= tax
            nation.treasury += tax
            nation.tax_collected_last_tick += tax


def government_spending_phase(world):
    """
    Deduct the weekly budget from the treasury.
    If the treasury cannot cover it, issue bonds to cover the shortfall.
    """
    for nation in world.nations.values():
        nation.spending_last_tick = nation.weekly_budget
        nation.bonds_issued_last_tick = 0.0
        if nation.weekly_budget <= 0:
            continue
        if nation.treasury >= nation.weekly_budget:
            nation.treasury -= nation.weekly_budget
        else:
            # Spend what we have, borrow the rest
            shortfall = nation.weekly_budget - nation.treasury
            nation.treasury = 0.0
            nation.outstanding_bonds += shortfall
            nation.bonds_issued_last_tick = shortfall


def pay_debt_interest(world):
    """
    Pay weekly interest on outstanding bonds and on legacy debt_total.
    If treasury cannot cover it, add unpaid interest to bonds (rolling over).
    """
    for nation in world.nations.values():
        nation.interest_paid_last_tick = 0.0
        # Interest on bonds we've issued
        bond_interest = nation.outstanding_bonds * nation.bond_interest_rate
        # Interest on legacy debt_total (treated as pre-existing bonds)
        legacy_interest = nation.debt_total * nation.bond_interest_rate
        total_interest = bond_interest + legacy_interest
        if total_interest <= 0:
            continue
        if nation.treasury >= total_interest:
            nation.treasury -= total_interest
            nation.interest_paid_last_tick = total_interest
        else:
            # Can't pay — roll the unpaid interest into new bonds
            unpaid = total_interest - nation.treasury
            nation.treasury = 0.0
            nation.outstanding_bonds += unpaid
            nation.interest_paid_last_tick = total_interest - unpaid


def government_finance_phase(world):
    collect_profit_tax(world)
    government_spending_phase(world)
    pay_debt_interest(world)