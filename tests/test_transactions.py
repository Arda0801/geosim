import pytest

from sim.engine import World
from sim.entities import Company, Commodity


def make_world():
    world = World()

    world.add_commodity(
        Commodity(
            id="fuel",
            name="Fuel",
            unit="litres",
            current_price=50,
            per_capita_daily_demand=0,
        )
    )

    world.add_company(
        Company(
            id="SELLER",
            name="Seller",
            home_nation_id="USA",
            sector="energy",
            cash=10000,
            production_capacity=1000,
            current_output=0,
            wage_cost_per_tick=0,
        )
    )

    world.add_company(
        Company(
            id="BUYER",
            name="Buyer",
            home_nation_id="USA",
            sector="manufacturing",
            cash=100000,
            production_capacity=1000,
            current_output=0,
            wage_cost_per_tick=0,
        )
    )

    world.add_inventory(
        owner_id="SELLER",
        commodity_id="fuel",
        region_id="PORT_USA",
        quantity=900,
    )

    return world


def test_successful_transaction():
    world = make_world()

    transaction = world.execute_transaction(
        transaction_id="T1",
        seller_id="SELLER",
        buyer_id="BUYER",
        commodity_id="fuel",
        quantity=900,
        price_per_unit=50,
        region_id="PORT_USA",
    )

    assert transaction.total_value == 45000

    assert world.companies["SELLER"].cash == 55000
    assert world.companies["BUYER"].cash == 55000

    assert world.get_inventory_quantity(
        "SELLER",
        "fuel",
        "PORT_USA",
    ) == 0

    assert world.get_inventory_quantity(
        "BUYER",
        "fuel",
        "PORT_USA",
    ) == 900


def test_insufficient_inventory():
    world = make_world()

    with pytest.raises(ValueError, match="insufficient inventory"):
        world.execute_transaction(
            transaction_id="T1",
            seller_id="SELLER",
            buyer_id="BUYER",
            commodity_id="fuel",
            quantity=1000,
            price_per_unit=50,
            region_id="PORT_USA",
        )


def test_insufficient_cash():
    world = make_world()

    with pytest.raises(ValueError, match="insufficient cash"):
        world.execute_transaction(
            transaction_id="T1",
            seller_id="SELLER",
            buyer_id="BUYER",
            commodity_id="fuel",
            quantity=900,
            price_per_unit=1000,
            region_id="PORT_USA",
        )