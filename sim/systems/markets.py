def market_phase(world):
    for market in world.markets.values():
        recent_shock = any(
            e.timestamp_hours >= world.current_hour - 24 and not e.applied is False
            for e in world.events
        )
        if recent_shock:
            market.volatility_index += 5.0
            market.index_value *= 0.98
        else:
            market.volatility_index = max(10.0, market.volatility_index * 0.95)
            market.index_value *= 1.001