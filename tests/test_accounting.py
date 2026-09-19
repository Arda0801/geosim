import unittest
from tests.helpers import make_production_world


class TestAccounting(unittest.TestCase):
    def test_profit_ledger_matches_cash_change(self):
        w = make_production_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", 5000)

        w.world.run_tick()
        cash_before = w.oil_co.cash
        w.world.run_tick()  # crude available, real production/sale/costs all happen this tick

        cash_after = w.oil_co.cash
        self.assertAlmostEqual(cash_after - cash_before, w.oil_co.profit_last_tick, places=2)


if __name__ == "__main__":
    unittest.main()