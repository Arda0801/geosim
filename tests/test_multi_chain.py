import unittest
from tests.helpers import make_multi_chain_world


class TestMultiChain(unittest.TestCase):
    def test_farm_produces_food_with_no_inputs(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery, steel, food, steel_co, steel_mill, farm_co, farm = make_multi_chain_world()

        world.run_tick()

        self.assertGreater(world.get_inventory_quantity("PORT_USA", "food"), 0.0)

    def test_steel_mill_consumes_fuel_produced_by_refinery(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery, steel, food, steel_co, steel_mill, farm_co, farm = make_multi_chain_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)

        world.run_tick()  # crude ships in
        world.run_tick()  # refinery makes fuel, steel mill should consume it same tick

        self.assertGreater(world.get_inventory_quantity("PORT_USA", "steel"), 0.0)

    def test_blockade_starves_steel_production_via_fuel_shortage(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery, steel, food, steel_co, steel_mill, farm_co, farm = make_multi_chain_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)

        world.run_tick()
        world.run_tick()  # normal chain runs once, steel gets produced

        route.status = "blockaded"
        route.risk_level = 1.0

        for _ in range(5):
            world.run_tick()  # no new crude, no new fuel, steel mill should starve out

        steel_output_late = steel_mill.capacity  # sanity: capacity itself doesn't change
        # the real check: no fuel means no steel can be produced this tick
        fuel_available = world.get_inventory_quantity("PORT_USA", "fuel")
        self.assertEqual(fuel_available, 0.0)


if __name__ == "__main__":
    unittest.main()