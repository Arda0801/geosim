import heapq

from sim.systems.accounting import charge_for_inputs


def _produce_with_input_sources(facility, world):
    if not facility.operational:
        return 0.0, {}

    max_production = facility.capacity * facility.efficiency
    possible_production = max_production

    for commodity_id, required_per_unit in facility.inputs.items():
        available = sum(
            inv.quantity
            for inv in world.get_inventories_in_region(facility.region_id, commodity_id)
        )
        if required_per_unit > 0:
            possible = available / required_per_unit
            possible_production = min(possible_production, possible)

    if possible_production <= 0:
        return 0.0, {}

    consumed_inputs = {}
    for commodity_id, required_per_unit in facility.inputs.items():
        amount_required = possible_production * required_per_unit
        remaining = amount_required
        for inv in world.get_inventories_in_region(facility.region_id, commodity_id):
            if remaining <= 0:
                break
            take = min(inv.quantity, remaining)
            world.remove_inventory(inv.owner_id, commodity_id, facility.region_id, take)
            consumed_inputs.setdefault(commodity_id, []).append((inv.owner_id, take))
            remaining -= take

    return possible_production, consumed_inputs


def produce(facility, world):
    produced, _ = _produce_with_input_sources(facility, world)
    return produced


def _production_order(world):
    facilities = list(world.production_facilities.values())
    facility_by_id = {facility.id: facility for facility in facilities}
    producers_by_output = {}
    for facility in facilities:
        for commodity_id in facility.outputs:
            producers_by_output.setdefault((facility.region_id, commodity_id), []).append(
                facility.id
            )

    dependencies = {facility.id: set() for facility in facilities}
    dependents = {facility.id: set() for facility in facilities}
    for facility in facilities:
        for commodity_id in facility.inputs:
            for producer_id in producers_by_output.get((facility.region_id, commodity_id), ()):
                if producer_id == facility.id or facility.id in dependents[producer_id]:
                    continue
                dependencies[facility.id].add(producer_id)
                dependents[producer_id].add(facility.id)

    ready = [
        facility_id
        for facility_id, required in dependencies.items()
        if not required
    ]
    heapq.heapify(ready)
    ordered_ids = []
    ordered_set = set()
    while ready:
        facility_id = heapq.heappop(ready)
        ordered_ids.append(facility_id)
        ordered_set.add(facility_id)
        for dependent_id in sorted(dependents[facility_id]):
            dependencies[dependent_id].discard(facility_id)
            if not dependencies[dependent_id]:
                heapq.heappush(ready, dependent_id)

    # Cyclic chains cannot be fully ordered; keep their fallback deterministic.
    ordered_ids.extend(sorted(set(facility_by_id) - ordered_set))
    return [facility_by_id[facility_id] for facility_id in ordered_ids]


def production_phase(world):
    for facility in _production_order(world):
        if not facility.operational:
            continue

        produced, consumed_inputs = _produce_with_input_sources(facility, world)
        if produced <= 0:
            continue

        company = world.companies[facility.company_id]
        company.current_output = produced
        charge_for_inputs(facility, produced, world, consumed_inputs)

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
