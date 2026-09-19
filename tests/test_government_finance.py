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
        w.world.add_inventory("PORT_USA", "crude_oil", 5000)

        treasury_before = w.usa.treasury
        w.world.run_tick()

        # Company should have made a profit (fuel sells for more than crude costs)
        self.assertGreater(w.oil_co.profit_last_tick, 0)
        # Nation should have collected tax on that profit
        self.assertGreater(w.usa.tax_collected_last_tick, 0)
        self.assertGreater(w.usa.treasury, treasury_before)

    def test_no_tax_when_company_loses_money(self):
        """A company with zero or negative profit pays no tax."""
        w = make_production_world()
        # Make the company lose money: expensive inputs, cheap outputs
        w.crude.current_price = 50.0
        w.fuel.current_price = 5.0
        w.world.add_inventory("PORT_IRN", "crude_oil", 5000)

        treasury_before = w.usa.treasury
        w.world.run_tick()

        # Company should have a loss (inputs cost more than outputs earn)
        self.assertLessEqual(w.oil_co.profit_last_tick, 0)
        # Nation should collect zero tax from this company
        # (treasury change comes only from spending/interest, not this company)
        self.assertLessEqual(w.usa.tax_collected_last_tick, 0)

    def test_government_spending_reduces_treasury(self):
        """Setting a weekly budget drains the treasury each tick."""
        w = make_production_world()
        w.usa.weekly_budget = 5000.0
        treasury_before = w.usa.treasury

        w.world.run_tick()

        # Treasury should have decreased by at least the budget
        # (minus any tax collected, plus/minus interest)
        self.assertLess(w.usa.treasury, treasury_before)
        self.assertEqual(w.usa.spending_last_tick, 5000.0)

    def test_bonds_issued_when_treasury_insufficient(self):
        """When spending exceeds treasury, bonds are issued to cover the gap."""
        w = make_production_world()
        w.usa.weekly_budget = 1_000_000.0  # far more than treasury
        w.usa.treasury = 10_000.0

        w.world.run_tick()

        # Treasury should be drained to 0 (or near 0 after tax/interest)
        self.assertLessEqual(w.usa.treasury, 100.0)
        # Bonds should have been issued
        self.assertGreater(w.usa.outstanding_bonds, 0)
        self.assertGreater(w.usa.bonds_issued_last_tick, 0)

    def test_debt_interest_accumulates(self):
        """Outstanding bonds generate interest payments each tick."""
        w = make_production_world()
        w.usa.weekly_budget = 0.0
        w.usa.outstanding_bonds = 100_000.0
        w.usa.treasury = 50_000.0

        w.world.run_tick()

        # Should have paid some interest
        self.assertGreater(w.usa.interest_paid_last_tick, 0)
        # Treasury should be lower after paying interest
        # (exact amount depends on tax collected, but it should be less than 50k + tax)
        self.assertLess(w.usa.treasury, 50_000.0 + w.usa.tax_collected_last_tick)

    def test_iran_also_pays_interest_on_legacy_debt(self):
        """Iran's existing debt_total should generate interest payments."""
        w = make_production_world()
        w.iran.weekly_budget = 0.0
        w.iran.treasury = 100_000.0  # give it money to pay interest

        w.world.run_tick()

        # Iran should be paying interest on its 10,000 debt_total
        self.assertGreater(w.iran.interest_paid_last_tick, 0)
        self.assertLess(w.iran.treasury, 100_000.0)


if __name__ == "__main__":
    unittest.main()