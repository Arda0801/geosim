def trade_phase(world):
    for route in world.routes.values():
        if route.status == "blockaded":
            route.current_flow = 0.0
            route.current_cost = route.base_cost * 3
            continue

        effective_capacity = route.capacity * (1 - route.risk_level)
        effective_cost = route.base_cost * (1 + route.risk_level * 2)
        route.current_flow = effective_capacity
        route.current_cost = effective_cost

        origin = route.origin_region_id
        destination = route.destination_region_id

        dest_region = world.regions.get(destination)
        if not dest_region:
            continue

        dest_used = world.get_region_storage_used(destination)
        dest_free = dest_region.storage_capacity - dest_used

        for (owner_id, commodity_id, region_id), inv in list(world.inventories.items()):
            if region_id != origin:
                continue

            shippable = min(inv.quantity, effective_capacity, dest_free)
            if shippable <= 0:
                continue

            world.remove_inventory(owner_id, commodity_id, origin, shippable)
            world.add_inventory(owner_id, commodity_id, destination, shippable)

            dest_free -= shippable
            effective_capacity -= shippable

            if effective_capacity <= 0:
                break