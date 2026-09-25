from sim.systems.accounting import charge_for_inputs, record_sale


def produce(facility, world):
    """
    Attempt to run one production facility for one tick.
    Returns the amount of production completed.
    """
    if not facility.operational:
        return 0.0
    max_production = facility.capacity * facility.efficiency
    possible_production = max_production
    for commodity_id, required_per_unit in facility.inputs.items():
        available = world.get_inventory_quantity(
            facility.region_id,
            commodity_id
        )
        if required_per_unit > 0:
            possible = available / required_per_unit
            possible_production = min(possible_production, possible)
    if possible_production <= 0:
        return 0.0
    for commodity_id, required_per_unit in facility.inputs.items():
        amount_required = possible_production * required_per_unit
        world.remove_inventory(
            facility.region_id,
            commodity_id,
            facility.region_id,
            amount_required
        )
    return possible_production


def production_phase(world):
    for facility in world.production_facilities.values():
        if not facility.operational:
            continue

        produced = produce(facility, world)
        if produced <= 0:
            continue

        company = world.companies[facility.company_id]
        company.current_output = produced
        charge_for_inputs(facility, produced, world)

        for commodity_id, amount_per_unit in facility.outputs.items():
            if amount_per_unit <= 0:
                continue
            world.add_inventory(
                owner_id=facility.company_id,
                commodity_id=commodity_id,
                region_id=facility.region_id,
                quantity=amount_per_unit * produced,
            )

        company.cash -= company.wage_cost_per_tick
        company.wage_costs_last_tick += company.wage_cost_per_tick
