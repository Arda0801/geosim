def produce(facility, world):
    """
    Attempt to run one production facility for one tick.

    Returns the amount of production completed.
    """

    if not facility.operational:
        return 0.0

    max_production = facility.capacity * facility.efficiency

    possible_production = max_production

    # Check whether we have enough inputs
    for commodity_id, required_per_unit in facility.inputs.items():

        available = world.get_inventory_quantity(
            facility.company_id,
            commodity_id
        )

        if required_per_unit > 0:
            possible = available / required_per_unit
            possible_production = min(
                possible_production,
                possible
            )

    if possible_production <= 0:
        return 0.0

    # Consume inputs
    for commodity_id, required_per_unit in facility.inputs.items():

        amount_required = (
            possible_production * required_per_unit
        )

        world.remove_inventory(
            facility.company_id,
            commodity_id,
            amount_required
        )

    # Produce outputs
    for commodity_id, output_per_unit in facility.outputs.items():

        amount_produced = (
            possible_production * output_per_unit
        )

        world.add_inventory(
            facility.company_id,
            commodity_id,
            amount_produced
        )

    return possible_production