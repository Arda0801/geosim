import unittest
from sim.entities import DemandProfile
from tests.helpers import make_multi_chain_world


class TestFullEconomy(unittest.TestCase):
    def test_food_and_fuel_both_generate_revenue_for_their_producers(self):
        w = make_multi_chain_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", "PORT_IRN", 5000)

        w.port_usa.population = 1_000_000
        w.fuel.per_capita_daily_demand = 0.005
        w.food.per_capita_daily_demand = 0.01

        w.world.add_demand_profile(DemandProfile(nation_id="USA", commodity_id="fuel"))
        w.world.add_demand_profile(DemandProfile(nation_id="USA", commodity_id="food"))

        w.world.run_tick()  # crude ships in
        farm_cash_before = w.farm_co.cash
        oil_cash_before = w.oil_co.cash

        print("\n--- After tick 1 (crude should have shipped) ---")
        print("PORT_USA crude:", w.world.get_inventory_quantity("PORT_USA", "crude_oil", "PORT_USA"))
        print("PORT_IRN crude:", w.world.get_inventory_quantity("PORT_IRN", "crude_oil", "PORT_IRN"))

        w.world.run_tick()  # farm sells food to demand, refinery makes fuel...

        print("\n--- DEBUG ---")
        print("Fuel price:", w.fuel.current_price)
        print("PORT_USA fuel (region):", w.world.get_inventory_quantity("PORT_USA", "fuel", "PORT_USA"))
        print("OILCO fuel (company):", w.world.get_total_inventory_for_owner("OILCO", "fuel"))
        print("Steel produced:", w.world.get_total_inventory_for_owner("STEELCO", "steel"))
        print("oil_co.total_revenue:", w.oil_co.total_revenue)
        print("oil_co.input_costs_last_tick:", w.oil_co.input_costs_last_tick)

        self.assertGreater(w.farm_co.cash, farm_cash_before)
        self.assertGreater(w.oil_co.total_revenue, 0.0)

    def test_blockade_starves_fuel_demand_and_spikes_price(self):
        w = make_multi_chain_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", "PORT_IRN", 5000)

        w.port_usa.population = 1_000_000
        w.fuel.per_capita_daily_demand = 0.01

        w.world.add_demand_profile(DemandProfile(nation_id="USA", commodity_id="fuel"))

        w.world.run_tick()
        w.world.run_tick()  # normal chain runs, fuel price should be roughly stable or drifting

        price_before_blockade = w.fuel.current_price

        w.route.status = "blockaded"
        w.route.risk_level = 1.0

        for _ in range(4):
            w.world.run_tick()  # no new crude, fuel supply dries up against ongoing demand

        self.assertGreater(w.fuel.current_price, price_before_blockade)


if __name__ == "__main__":
    unittest.main()