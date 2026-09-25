import unittest
from tests.helpers import make_production_world
from sim.systems.accounting import close_books, open_books, record_sale
from sim.systems.government import government_finance_phase


class TestAccounting(unittest.TestCase):
    def test_profit_ledger_includes_corporate_tax(self):
        w = make_production_world()
        company = w.oil_co
        cash_before = company.cash
        open_books(w.world)
        record_sale(company, w.fuel, 100.0)
        company.cash -= 200.0
        company.input_costs_last_tick = 200.0
        company.cash -= 100.0
        company.wage_costs_last_tick = 100.0

        close_books(w.world)
        government_finance_phase(w.world)

        self.assertAlmostEqual(
            company.cash - cash_before,
            company.profit_last_tick,
            places=2,
        )

    def test_profit_ledger_matches_cash_change(self):
        w = make_production_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", "PORT_IRN", 5000)

        w.world.run_tick()
        cash_before = w.oil_co.cash
        w.world.run_tick()  # crude available, real production/sale/costs all happen this tick

        cash_after = w.oil_co.cash
        self.assertAlmostEqual(cash_after - cash_before, w.oil_co.profit_last_tick, places=2)


if __name__ == "__main__":
    unittest.main()