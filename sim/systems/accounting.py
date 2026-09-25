def charge_for_inputs(facility, produced, world, consumed_inputs) -> float:
    """Company pays spot price for every input unit its facility consumed."""
    company = world.companies.get(facility.company_id)
    cost = 0.0

    for commodity_id, sources in consumed_inputs.items():
        commodity = world.commodities.get(commodity_id)
        if not commodity:
            continue

        input_quantity = sum(quantity for _, quantity in sources)
        input_cost = input_quantity * commodity.current_price
        cost += input_cost
        if company and input_cost:
            company.cash -= input_cost
            company.input_costs_last_tick += input_cost

            for owner_id, quantity in sources:
                supplier = world.companies.get(owner_id)
                if supplier and supplier.id != company.id:
                    record_sale(supplier, commodity, quantity)
    return cost

def record_sale(company, commodity, quantity, price_per_unit=None) -> float:
    sale_price = (
        commodity.current_price if price_per_unit is None else price_per_unit
    )
    revenue = quantity * sale_price
    company.cash += revenue
    company.revenue_last_tick += revenue
    return revenue

def close_books(world):
    """End of tick: finalize P&L and update cumulative totals."""
    for c in world.companies.values():
        c.profit_last_tick = (c.revenue_last_tick - c.input_costs_last_tick
                              - c.wage_costs_last_tick - c.interest_paid_last_tick
                              - c.principal_paid_last_tick
                              - c.tax_paid_last_tick)
        c.total_revenue += c.revenue_last_tick
        c.total_profit += c.profit_last_tick


def open_books(world):
    """Clear current-tick accounting accumulators before a new tick starts."""
    for company in world.companies.values():
        company.revenue_last_tick = company.input_costs_last_tick = 0.0
        company.wage_costs_last_tick = company.interest_paid_last_tick = 0.0
        company.principal_paid_last_tick = company.tax_paid_last_tick = 0.0