"""
Market clearing system: generates orders, matches them, discovers prices.

Called once per economic tick (week) from World.run_tick().
Uses a uniform-price double auction: all matched trades execute
at the same clearing price.
"""

from sim.entities import Order

def generate_sell_orders(world):
    for (owner_id, commodity_id, region_id), inv in world.inventories.items():
        if inv.quantity <= 0:
            continue

        if owner_id not in world.companies and owner_id not in world.regions:
            continue

        commodity = world.commodities.get(commodity_id)
        if not commodity:
            continue

        order = Order(
            id=f"SELL_{world.tick_number}_{owner_id}_{commodity_id}_{region_id}",
            order_type="sell",
            commodity_id=commodity_id,
            owner_id=owner_id,
            region_id=region_id,
            quantity=inv.quantity,
            price=commodity.current_price * 0.5,
            tick_placed=world.tick_number,
        )
        world.orders[order.id] = order


def generate_buy_orders(world):
    """
    Population demand generates buy orders from DemandProfile entries.
    Buy price = current market price × 2 (willing to pay up to 2x current).
    This represents inelastic demand — people need fuel/food regardless.
    """
    for profile in world.demand_profiles:
        commodity = world.commodities.get(profile.commodity_id)
        if not commodity:
            continue
        nation = world.nations.get(profile.nation_id)
        if not nation:
            continue
        # Create region-specific orders so matched goods have a valid destination.
        nation_regions = [
            r for r in world.regions.values()
            if r.owner_nation_id == profile.nation_id
        ]
        for region in nation_regions:
            weekly_demand = (
                region.population * commodity.per_capita_daily_demand * 7
            )
            if weekly_demand <= 0:
                continue
            # Buy at up to 2x current price — inelastic demand placeholder
            order = Order(
                id=(
                    f"BUY_{world.tick_number}_{profile.nation_id}_"
                    f"{profile.commodity_id}_{region.id}"
                ),
                order_type="buy",
                commodity_id=profile.commodity_id,
                owner_id=profile.nation_id,
                region_id=region.id,
                quantity=weekly_demand,
                price=commodity.current_price * 2.0,
                tick_placed=world.tick_number,
            )
            world.orders[order.id] = order


def clear_market(world):
    """
    Match buy and sell orders for each commodity using a uniform-price
    double auction. All matched trades execute at the same clearing price.
    Updates commodity prices based on where supply meets demand.
    """
    pending_statuses = {"open", "partially_filled"}
    for order in world.orders.values():
        if order.tick_placed < world.tick_number and order.status in pending_statuses:
            order.status = "expired"

    for commodity in world.commodities.values():
        commodity.last_buy_quantity = 0.0
        commodity.last_sell_quantity = 0.0
        commodity.last_volume_traded = 0.0
        commodity.last_clearing_price = commodity.current_price

    orders_by_commodity = {}
    for order in world.orders.values():
        if (
            order.tick_placed != world.tick_number
            or order.status not in pending_statuses
            or order.quantity <= order.filled_quantity
        ):
            continue
        book = orders_by_commodity.setdefault(order.commodity_id, {"buy": [], "sell": []})
        book[order.order_type].append(order)

    for commodity_id, book in orders_by_commodity.items():
        commodity = world.commodities.get(commodity_id)
        if not commodity:
            continue

        buys = sorted(book["buy"], key=lambda order: order.price, reverse=True)
        sells = sorted(book["sell"], key=lambda order: order.price)
        buy_total = sum(order.quantity - order.filled_quantity for order in buys)
        sell_total = sum(order.quantity - order.filled_quantity for order in sells)
        commodity.last_buy_quantity = buy_total
        commodity.last_sell_quantity = sell_total

        if not buys or not sells:
            if buy_total > 0 and sell_total == 0:
                commodity.current_price *= 1.05
            elif sell_total > 0 and buy_total == 0:
                commodity.current_price *= 0.95
            continue

        buy_remaining = [
            (order, order.quantity - order.filled_quantity) for order in buys
        ]
        sell_remaining = [
            (order, order.quantity - order.filled_quantity) for order in sells
        ]
        matches = []
        buy_index = 0
        sell_index = 0
        clearing_price = commodity.current_price

        while buy_index < len(buy_remaining) and sell_index < len(sell_remaining):
            buy_order, buy_quantity = buy_remaining[buy_index]
            sell_order, sell_quantity = sell_remaining[sell_index]
            if buy_order.price < sell_order.price:
                break

            matched_quantity = min(buy_quantity, sell_quantity)
            matches.append((buy_order, sell_order, matched_quantity))
            clearing_price = (buy_order.price + sell_order.price) / 2
            buy_remaining[buy_index] = (buy_order, buy_quantity - matched_quantity)
            sell_remaining[sell_index] = (sell_order, sell_quantity - matched_quantity)

            if buy_remaining[buy_index][1] <= 0:
                buy_index += 1
            if sell_remaining[sell_index][1] <= 0:
                sell_index += 1

        total_traded = sum(quantity for _, _, quantity in matches)
        for buy_order, sell_order, quantity in matches:
            execute_trade(world, buy_order, sell_order, commodity_id, quantity, clearing_price)

        commodity.last_volume_traded = total_traded
        if total_traded > 0:
            commodity.last_clearing_price = clearing_price
            if sell_total > buy_total:
                commodity.current_price = min(clearing_price, commodity.current_price * 0.95)
            elif buy_total > sell_total:
                commodity.current_price = max(clearing_price, commodity.current_price * 1.05)
            else:
                commodity.current_price = clearing_price
        elif buy_total > sell_total:
            commodity.current_price *= 1.02
        elif sell_total > buy_total:
            commodity.current_price *= 0.98


def execute_trade(world, buy_order, sell_order, commodity_id, quantity, price):
    from sim.systems.accounting import record_sale

    commodity = world.commodities.get(commodity_id)
    if not commodity:
        return

    world.remove_inventory(sell_order.owner_id, commodity_id, sell_order.region_id, quantity)

    if buy_order.order_type == "buy" and buy_order.owner_id in world.companies:
        world.add_inventory(buy_order.owner_id, commodity_id, buy_order.region_id, quantity)
    # else: population buying — goods are consumed, no inventory added

    seller = world.companies.get(sell_order.owner_id)
    if seller:
        record_sale(seller, commodity, quantity, price)

    sell_order.filled_quantity += quantity
    buy_order.filled_quantity += quantity

    if sell_order.filled_quantity >= sell_order.quantity:
        sell_order.status = "filled"
    else:
        sell_order.status = "partially_filled"

    if buy_order.filled_quantity >= buy_order.quantity:
        buy_order.status = "filled"
    else:
        buy_order.status = "partially_filled"


def market_clearing_phase(world):
    """
    Main entry point: generate orders, clear the market, discover prices.
    Called once per tick from World.run_tick().
    """
    generate_sell_orders(world)
    generate_buy_orders(world)
    clear_market(world)