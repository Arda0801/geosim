"""
Market clearing system: generates orders, matches them, discovers prices.

Called once per economic tick (week) from World.run_tick().
Uses a uniform-price double auction: all matched trades execute
at the same clearing price.
"""

from sim.entities import Order

def generate_sell_orders(world):
    """
    Region and company inventories can both offer goods on the market.
    Sell price = current market price × 0.5 (accepting a discount to clear stock).
    """
    for (owner_id, commodity_id, region_id), inv in world.inventories.items():
        if inv.quantity <= 0:
            continue

        # Only canonical local stock should be sold at market: owner and region are the same.
        if owner_id != region_id:
            continue

        if owner_id not in world.companies and owner_id not in world.regions:
            continue

        commodity = world.commodities.get(commodity_id)
        if not commodity:
            continue

        order = Order(
            id=f"SELL_{world.tick_number}_{owner_id}_{commodity_id}",
            order_type="sell",
            commodity_id=commodity_id,
            owner_id=owner_id,
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
        # Calculate weekly demand (7 days worth)
        nation_regions = [
            r for r in world.regions.values()
            if r.owner_nation_id == profile.nation_id
        ]
        weekly_demand = sum(
            r.population * commodity.per_capita_daily_demand * 7
            for r in nation_regions
        )
        if weekly_demand <= 0:
            continue
        # Buy at up to 2x current price — inelastic demand placeholder
        order = Order(
            id=f"BUY_{world.tick_number}_{profile.nation_id}_{profile.commodity_id}",
            order_type="buy",
            commodity_id=profile.commodity_id,
            owner_id=profile.nation_id,
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
    # Group orders by commodity
    orders_by_commodity = {}
    for order in world.orders.values():
        if order.status != "open":
            continue
        if order.commodity_id not in orders_by_commodity:
            orders_by_commodity[order.commodity_id] = {"buy": [], "sell": []}
        orders_by_commodity[order.commodity_id][order.order_type].append(order)

    for commodity_id, book in orders_by_commodity.items():
        commodity = world.commodities.get(commodity_id)
        if not commodity:
            continue

        buys = sorted(book["buy"], key=lambda o: o.price, reverse=True)  # highest first
        sells = sorted(book["sell"], key=lambda o: o.price)  # lowest first

        commodity.last_buy_quantity = sum(o.quantity for o in buys)
        commodity.last_sell_quantity = sum(o.quantity for o in sells)

        if not buys or not sells:
            # No trades possible — adjust price based on imbalance
            if commodity.last_buy_quantity > 0 and commodity.last_sell_quantity == 0:
                # Demand but no supply — price should rise
                commodity.current_price *= 1.05
            elif commodity.last_buy_quantity == 0 and commodity.last_sell_quantity > 0:
                # Supply but no demand — price should fall
                commodity.current_price *= 0.95
            commodity.last_volume_traded = 0.0
            continue

        # Find clearing price and quantity using a simple crossing algorithm
        # Walk down the buy curve and up the sell curve simultaneously
        total_traded = 0.0
        clearing_price = commodity.current_price  # default

        buy_remaining = [(o, o.quantity) for o in buys]
        sell_remaining = [(o, o.quantity) for o in sells]

        buy_idx = 0
        sell_idx = 0

        while buy_idx < len(buy_remaining) and sell_idx < len(sell_remaining):
            buy_order, buy_qty = buy_remaining[buy_idx]
            sell_order, sell_qty = sell_remaining[sell_idx]

            # Check if this pair can trade (buy price >= sell price)
            if buy_order.price < sell_order.price:
                break  # no more matching possible

            # Trade quantity is the minimum of remaining quantities
            trade_qty = min(buy_qty, sell_qty)
            clearing_price = (buy_order.price + sell_order.price) / 2  # midpoint

            # Execute the trade
            execute_trade(world, buy_order, sell_order, commodity_id, trade_qty, clearing_price)

            total_traded += trade_qty

            # Update remaining quantities
            buy_remaining[buy_idx] = (buy_order, buy_qty - trade_qty)
            sell_remaining[sell_idx] = (sell_order, sell_qty - trade_qty)

            # Move to next order if this one is fully filled
            if buy_remaining[buy_idx][1] <= 0:
                buy_idx += 1
            if sell_remaining[sell_idx][1] <= 0:
                sell_idx += 1

        # Update commodity market data
        commodity.last_clearing_price = clearing_price if total_traded > 0 else commodity.current_price
        commodity.last_volume_traded = total_traded

        # Price discovery: the clearing price becomes the new market price,
        # but oversupply/shortage should push the result away from the raw midpoint.
        if total_traded > 0:
            if commodity.last_sell_quantity > commodity.last_buy_quantity:
                commodity.current_price = min(clearing_price, commodity.current_price * 0.95)
            elif commodity.last_buy_quantity > commodity.last_sell_quantity:
                commodity.current_price = max(clearing_price, commodity.current_price * 1.05)
            else:
                commodity.current_price = clearing_price
        else:
            # No trades — adjust based on order imbalance
            if commodity.last_buy_quantity > commodity.last_sell_quantity:
                commodity.current_price *= 1.02  # more demand than supply
            elif commodity.last_sell_quantity > commodity.last_buy_quantity:
                commodity.current_price *= 0.98  # more supply than demand

        # Mark expired orders
        for order in world.orders.values():
            if order.tick_placed < world.tick_number and order.status == "open":
                order.status = "expired"


def execute_trade(world, buy_order, sell_order, commodity_id, quantity, price):
    """
    Execute a matched trade: transfer inventory, record cash flows.
    """
    from sim.systems.accounting import record_sale

    commodity = world.commodities.get(commodity_id)
    if not commodity:
        return

    # Transfer inventory from seller to buyer
    # For now: remove from seller's inventory (goods are consumed by population)
    # or keep in region inventory if the buyer is a company needing inputs
    if buy_order.order_type == "buy" and buy_order.owner_id in world.companies:
        # Company buying inputs — add to their inventory
        world.remove_inventory(sell_order.owner_id, commodity_id, quantity)
        world.add_inventory(buy_order.owner_id, commodity_id, quantity)
    else:
        # Population buying — goods are consumed
        world.remove_inventory(sell_order.owner_id, commodity_id, quantity)

    # Record the sale for the seller's P&L
    seller = world.companies.get(sell_order.owner_id)
    if seller:
        record_sale(seller, commodity, quantity)

    # Update order statuses
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