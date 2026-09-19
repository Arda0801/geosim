import unittest
from sim.entities import DemandProfile
from tests.helpers import make_production_world


class TestProduction(unittest.TestCase):
    def test_refinery_converts_crude_to_fuel_and_sells_at_market_price(self):
        w = make_production_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", 5000)
        w.port_usa.population = 1_000_000
        w.fuel.per_capita_daily_demand = 0.01
        w.world.add_demand_profile(DemandProfile(nation_id="USA", commodity_id="fuel"))

        w.world.run_tick()  # ship crude in (but too late for this tick's production)
        cash_before = w.oil_co.cash

        w.world.run_tick()  # now crude is available, refinery should produce and sell to demand

        self.assertGreater(w.oil_co.cash, cash_before)

    def test_refinery_offline_produces_nothing(self):
        w = make_production_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", 5000)
        w.world.run_tick()
        w.world.run_tick()

        w.refinery.operational = False
        cash_before = w.oil_co.cash

        w.world.run_tick()

        self.assertLessEqual(w.oil_co.cash, cash_before)


if __name__ == "__main__":
    unittest.main()