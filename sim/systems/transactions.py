from sim.entities import Transaction


def execute_transaction(
    world,
    transaction_id,
    seller_id,
    buyer_id,
    commodity_id,
    quantity,
    price_per_unit,
    region_id,
) -> Transaction:
    if quantity <= 0:
        raise ValueError("Transaction quantity must be positive")

    if price_per_unit < 0:
        raise ValueError("Price cannot be negative")

    if seller_id not in world.companies:
        raise ValueError("Seller does not exist")

    if buyer_id not in world.companies:
        raise ValueError("Buyer does not exist")

    seller = world.companies[seller_id]
    buyer = world.companies[buyer_id]
    total_value = quantity * price_per_unit

    available = world.get_inventory_quantity(seller_id, commodity_id, region_id)
    if available < quantity:
        raise ValueError("Seller has insufficient inventory")

    if buyer.cash < total_value:
        raise ValueError("Buyer has insufficient cash")

    world.remove_inventory(seller_id, commodity_id, region_id, quantity)
    world.add_inventory(buyer_id, commodity_id, region_id, quantity)
    seller.cash += total_value
    buyer.cash -= total_value

    transaction = Transaction(
        id=transaction_id,
        seller_id=seller_id,
        buyer_id=buyer_id,
        commodity_id=commodity_id,
        quantity=quantity,
        price_per_unit=price_per_unit,
        total_value=total_value,
        timestamp_hours=world.current_hour,
        status="completed",
    )
    world.add_transaction(transaction)
    return transaction