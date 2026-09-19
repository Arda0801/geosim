import unittest
from sim.entities import DemandProfile
from tests.helpers import make_multi_chain_world


class TestFullEconomy(unittest.TestCase):
    def test_food_and_fuel_both_generate_revenue_for_their_producers(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery, steel, food, steel_co, steel_mill, farm_co, farm = make_multi_chain_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)

        port_usa.population = 1_000_000
        fuel.per_capita_daily_demand = 0.005
        food.per_capita_daily_demand = 0.01

        world.add_demand_profile(DemandProfile(nation_id="USA", commodity_id="fuel"))
        world.add_demand_profile(DemandProfile(nation_id="USA", commodity_id="food"))

        world.run_tick()  # crude ships in
        farm_cash_before = farm_co.cash
        oil_cash_before = oil_co.cash

        world.run_tick()  # farm sells food to demand, refinery makes fuel (steel mill takes some, demand takes rest)

        self.assertGreater(farm_co.cash, farm_cash_before)
        # oil_co pays for crude + wages + interest, but should also earn from fuel demand
        # net direction depends on tuning, so just confirm revenue was recorded, not necessarily net-positive cash
        self.assertGreater(oil_co.revenue_last_tick, 0.0)

    def test_blockade_starves_fuel_demand_and_spikes_price(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery, steel, food, steel_co, steel_mill, farm_co, farm = make_multi_chain_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)

        port_usa.population = 1_000_000
        fuel.per_capita_daily_demand = 0.01

        world.add_demand_profile(DemandProfile(nation_id="USA", commodity_id="fuel"))

        world.run_tick()
        world.run_tick()  # normal chain runs, fuel price should be roughly stable or drifting

        price_before_blockade = fuel.current_price

        route.status = "blockaded"
        route.risk_level = 1.0

        for _ in range(4):
            world.run_tick()  # no new crude, fuel supply dries up against ongoing demand

        self.assertGreater(fuel.current_price, price_before_blockade)


if __name__ == "__main__":
    unittest.main()