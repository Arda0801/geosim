import unittest
from sim.entities import DemandProfile
from tests.helpers import make_production_world


class TestProduction(unittest.TestCase):
    def test_refinery_converts_crude_to_fuel_and_sells_at_market_price(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery = make_production_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)
        port_usa.population = 1_000_000
        fuel.per_capita_daily_demand = 0.01
        world.add_demand_profile(DemandProfile(nation_id="USA", commodity_id="fuel"))

        world.run_tick()  # ship crude in (but too late for this tick's production)
        cash_before = oil_co.cash

        world.run_tick()  # now crude is available, refinery should produce and sell to demand

        self.assertGreater(oil_co.cash, cash_before)

    def test_refinery_offline_produces_nothing(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery = make_production_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)
        world.run_tick()
        world.run_tick()

        refinery.operational = False
        cash_before = oil_co.cash

        world.run_tick()

        self.assertLessEqual(oil_co.cash, cash_before)


if __name__ == "__main__":
    unittest.main()