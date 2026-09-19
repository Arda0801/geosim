import unittest
from sim.entities import DemandProfile
from tests.helpers import make_basic_world, make_production_world


class TestDemandPricing(unittest.TestCase):
    def test_price_drops_when_supply_exceeds_demand(self):
        w = make_basic_world()
        w.world.add_inventory("PORT_USA", "fuel", 5000)
        w.port_usa.population = 100  # tiny population, minimal real demand
        w.fuel.per_capita_daily_demand = 0.001

        demand = DemandProfile(nation_id="USA", commodity_id="fuel")
        w.world.add_demand_profile(demand)

        price_before = w.fuel.current_price
        w.world.run_tick()

        self.assertLess(w.fuel.current_price, price_before)

    def test_price_rises_under_scarcity(self):
        w = make_production_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", 5000)
        w.port_usa.population = 50_000_000  # huge population, demand will outstrip supply
        w.fuel.per_capita_daily_demand = 0.01

        demand = DemandProfile(nation_id="USA", commodity_id="fuel")
        w.world.add_demand_profile(demand)

        price_before = w.fuel.current_price
        w.world.run_tick()
        w.world.run_tick()

        self.assertGreater(w.fuel.current_price, price_before)


if __name__ == "__main__":
    unittest.main()