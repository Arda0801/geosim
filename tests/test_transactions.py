import unittest

from sim.engine import World
from sim.entities import Company, Commodity


def make_transaction_world():
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


class TestTransactions(unittest.TestCase):
    def test_successful_transaction(self):
        world = make_transaction_world()

        transaction = world.execute_transaction(
            transaction_id="T1",
            seller_id="SELLER",
            buyer_id="BUYER",
            commodity_id="fuel",
            quantity=900,
            price_per_unit=50,
            region_id="PORT_USA",
        )

        self.assertEqual(transaction.total_value, 45000)
        self.assertEqual(world.companies["SELLER"].cash, 55000)
        self.assertEqual(world.companies["BUYER"].cash, 55000)
        self.assertEqual(
            world.get_inventory_quantity("SELLER", "fuel", "PORT_USA"), 0
        )
        self.assertEqual(
            world.get_inventory_quantity("BUYER", "fuel", "PORT_USA"), 900
        )

    def test_insufficient_inventory_raises(self):
        world = make_transaction_world()

        with self.assertRaises(ValueError):
            world.execute_transaction(
                transaction_id="T1",
                seller_id="SELLER",
                buyer_id="BUYER",
                commodity_id="fuel",
                quantity=1000,
                price_per_unit=50,
                region_id="PORT_USA",
            )

    def test_insufficient_cash_raises(self):
        world = make_transaction_world()

        with self.assertRaises(ValueError):
            world.execute_transaction(
                transaction_id="T1",
                seller_id="SELLER",
                buyer_id="BUYER",
                commodity_id="fuel",
                quantity=900,
                price_per_unit=1000,
                region_id="PORT_USA",
            )


if __name__ == "__main__":
    unittest.main()