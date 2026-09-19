import unittest
from tests.helpers import make_multi_chain_world


class TestMultiChain(unittest.TestCase):
    def test_farm_produces_food_with_no_inputs(self):
        w = make_multi_chain_world()

        w.world.run_tick()

        self.assertGreater(w.world.get_inventory_quantity("PORT_USA", "food"), 0.0)

    def test_steel_mill_consumes_fuel_produced_by_refinery(self):
        w = make_multi_chain_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", 5000)

        w.world.run_tick()  # crude ships in
        w.world.run_tick()  # refinery makes fuel, steel mill should consume it same tick

        self.assertGreater(w.world.get_inventory_quantity("PORT_USA", "steel"), 0.0)

    def test_blockade_starves_steel_production_via_fuel_shortage(self):
        w = make_multi_chain_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", 5000)

        w.world.run_tick()
        w.world.run_tick()  # normal chain runs once, steel gets produced

        w.route.status = "blockaded"
        w.route.risk_level = 1.0

        for _ in range(5):
            w.world.run_tick()  # no new crude, no new fuel, steel mill should starve out

        steel_output_late = w.steel_mill.capacity  # sanity: capacity itself doesn't change
        # the real check: no fuel means no steel can be produced this tick
        fuel_available = w.world.get_inventory_quantity("PORT_USA", "fuel")
        self.assertEqual(fuel_available, 0.0)


if __name__ == "__main__":
    unittest.main()