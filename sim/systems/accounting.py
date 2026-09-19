def charge_for_inputs(facility, produced, world) -> float:
    """Company pays spot price for every input unit its facility consumed."""
    cost = sum(produced * req * world.commodities[cid].current_price
               for cid, req in facility.inputs.items()
               if cid in world.commodities)
    company = world.companies.get(facility.company_id)
    if company and cost:
        company.cash -= cost
        company.input_costs_last_tick += cost
    return cost

def record_sale(company, commodity, quantity) -> float:
    revenue = quantity * commodity.current_price
    company.cash += revenue
    company.revenue_last_tick += revenue
    return revenue

def close_books(world):
    """End of tick: finalize P&L, update cumulative totals, reset accumulators."""
    for c in world.companies.values():
        c.profit_last_tick = (c.revenue_last_tick - c.input_costs_last_tick
                              - c.wage_costs_last_tick - c.interest_paid_last_tick
                              - c.principal_paid_last_tick
                              - c.tax_paid_last_tick)
        c.total_revenue += c.revenue_last_tick
        c.total_profit += c.profit_last_tick
        c.revenue_last_tick = c.input_costs_last_tick = 0.0
        c.wage_costs_last_tick = c.interest_paid_last_tick = 0.0
        c.principal_paid_last_tick = c.tax_paid_last_tick = 0.0