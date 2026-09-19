import unittest
from tests.helpers import make_production_world


class TestAccounting(unittest.TestCase):
    def test_profit_ledger_matches_cash_change(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery = make_production_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)

        world.run_tick()
        cash_before = oil_co.cash
        world.run_tick()  # crude available, real production/sale/costs all happen this tick

        cash_after = oil_co.cash
        self.assertAlmostEqual(cash_after - cash_before, oil_co.profit_last_tick, places=2)


if __name__ == "__main__":
    unittest.main()