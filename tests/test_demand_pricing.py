import unittest
from sim.entities import DemandProfile
from tests.helpers import make_basic_world, make_production_world


class TestDemandPricing(unittest.TestCase):
    def test_price_drops_when_supply_exceeds_demand(self):
        world, usa, iran, port_usa, port_iran, crude, fuel = make_basic_world()
        world.add_inventory("PORT_USA", "fuel", 5000)
        port_usa.population = 100  # tiny population, minimal real demand
        fuel.per_capita_daily_demand = 0.001

        demand = DemandProfile(nation_id="USA", commodity_id="fuel")
        world.add_demand_profile(demand)

        price_before = fuel.current_price
        world.run_tick()

        self.assertLess(fuel.current_price, price_before)

    def test_price_rises_under_scarcity(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery = make_production_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)
        port_usa.population = 50_000_000  # huge population, demand will outstrip supply
        fuel.per_capita_daily_demand = 0.01

        demand = DemandProfile(nation_id="USA", commodity_id="fuel")
        world.add_demand_profile(demand)

        price_before = fuel.current_price
        world.run_tick()
        world.run_tick()

        self.assertGreater(fuel.current_price, price_before)


if __name__ == "__main__":
    unittest.main()