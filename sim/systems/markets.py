def _event_affects_market(world, event, market):
    target_id = event.target_id
    if target_id == market.nation_id:
        return True

    target_market = world.markets.get(target_id)
    if target_market:
        return target_market.nation_id == market.nation_id

    target_company = world.companies.get(target_id)
    if target_company:
        return target_company.home_nation_id == market.nation_id

    target_region_id = target_id
    target_district = world.districts.get(target_id)
    if target_district:
        target_region_id = target_district.region_id

    target_region = world.regions.get(target_region_id)
    if target_region:
        return target_region.owner_nation_id == market.nation_id

    target_route = world.routes.get(target_id)
    if target_route:
        return any(
            region_id in world.regions
            and world.regions[region_id].owner_nation_id == market.nation_id
            for region_id in (
                target_route.origin_region_id,
                target_route.destination_region_id,
            )
        )

    return False


def market_phase(world):
    for market in world.markets.values():
        recent_shock = any(
            e.applied
            and world.current_hour - 24 <= e.timestamp_hours <= world.current_hour
            and _event_affects_market(world, e, market)
            for e in world.events
        )
        if recent_shock:
            market.volatility_index += 5.0
            market.index_value *= 0.98
        else:
            market.volatility_index = max(10.0, market.volatility_index * 0.95)
            market.index_value *= 1.001