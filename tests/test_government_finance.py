import unittest
from sim.entities import DemandProfile
from tests.helpers import make_production_world


class TestGovernmentFinance(unittest.TestCase):

    def test_profit_tax_collected_when_company_profitable(self):
        """A company with positive profit pays tax; nation treasury increases."""
        w = make_production_world()
        w.crude.current_price = 10.0
        w.fuel.current_price = 20.0
        w.port_usa.population = 100_000
        w.fuel.per_capita_daily_demand = 0.01
        w.world.add_demand_profile(
            DemandProfile(nation_id="USA", commodity_id="fuel")
        )
        w.world.add_inventory("PORT_USA", "crude_oil", "PORT_USA", 5000)

        treasury_before = w.usa.treasury
        w.world.run_tick()

        self.assertGreater(w.oil_co.profit_last_tick, 0)
        self.assertGreater(w.usa.tax_collected_last_tick, 0)
        self.assertGreater(w.usa.treasury, treasury_before)

    def test_no_tax_when_company_loses_money(self):
        """A company with zero or negative profit pays no tax."""
        w = make_production_world()
        w.crude.current_price = 50.0
        w.fuel.current_price = 5.0
        w.world.add_inventory("PORT_IRN", "crude_oil", "PORT_IRN", 5000)

        treasury_before = w.usa.treasury
        w.world.run_tick()

        self.assertLessEqual(w.oil_co.profit_last_tick, 0)
        self.assertLessEqual(w.usa.tax_collected_last_tick, 0)

    def test_government_spending_reduces_treasury(self):
        """Setting a weekly budget drains the treasury each tick."""
        w = make_production_world()
        w.usa.weekly_budget = 5000.0
        treasury_before = w.usa.treasury

        w.world.run_tick()

        self.assertLess(w.usa.treasury, treasury_before)
        self.assertEqual(w.usa.spending_last_tick, 5000.0)

    def test_bonds_issued_when_treasury_insufficient(self):
        """When spending exceeds treasury, bonds are issued to cover the gap."""
        w = make_production_world()
        w.usa.weekly_budget = 1_000_000.0
        w.usa.treasury = 10_000.0

        w.world.run_tick()

        self.assertLessEqual(w.usa.treasury, 100.0)
        self.assertGreater(w.usa.outstanding_bonds, 0)
        self.assertGreater(w.usa.bonds_issued_last_tick, 0)

    def test_debt_interest_accumulates(self):
        """Outstanding bonds generate interest payments each tick."""
        w = make_production_world()
        w.usa.weekly_budget = 0.0
        w.usa.outstanding_bonds = 100_000.0
        w.usa.treasury = 50_000.0

        w.world.run_tick()

        self.assertGreater(w.usa.interest_paid_last_tick, 0)
        self.assertLess(w.usa.treasury, 50_000.0 + w.usa.tax_collected_last_tick)

    def test_iran_also_pays_interest_on_legacy_debt(self):
        """Iran's existing debt_total should generate interest payments."""
        w = make_production_world()
        w.iran.weekly_budget = 0.0
        w.iran.treasury = 100_000.0

        w.world.run_tick()

        self.assertGreater(w.iran.interest_paid_last_tick, 0)
        self.assertLess(w.iran.treasury, 100_000.0)


if __name__ == "__main__":
    unittest.main()