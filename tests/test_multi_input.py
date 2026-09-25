import unittest
from tests.helpers import make_full_industrial_world


class TestMultiInput(unittest.TestCase):
    def test_munitions_plant_consumes_both_steel_and_fuel(self):
        w = make_full_industrial_world()

        # seed steel and fuel directly so we isolate the munitions plant's behavior
        w.world.add_inventory("PORT_USA", "steel", "PORT_USA", 1000)
        w.world.add_inventory("PORT_USA", "fuel", "PORT_USA", 1000)

        w.world.run_tick()

        munitions_made = w.world.get_region_inventory_quantity("PORT_USA", "munitions")
        self.assertGreater(munitions_made, 0.0)

        # capacity=200, so at most 200 units produced this tick, output ratio 0.5 -> 100 munitions max
        self.assertLessEqual(munitions_made, 100.0)

    def test_scarcest_input_bottlenecks_production(self):
        w = make_full_industrial_world()

        # plenty of fuel, but only enough steel for 50 units (needs 2 steel/unit)
        w.steel_mill.operational = False
        w.world.add_inventory("PORT_USA", "steel", "PORT_USA", 100)
        w.world.add_inventory("PORT_USA", "fuel", "PORT_USA", 1000)

        w.world.run_tick()

        munitions_made = w.world.get_region_inventory_quantity("PORT_USA", "munitions")
        # 100 steel / 2 per unit = 50 units possible, output ratio 0.5 -> 25 munitions
        self.assertAlmostEqual(munitions_made, 25.0, places=1)

        # steel should be fully consumed, fuel should have leftover
        self.assertAlmostEqual(w.world.get_region_inventory_quantity("PORT_USA", "steel"), 0.0, places=1)
        self.assertGreater(w.world.get_region_inventory_quantity("PORT_USA", "fuel"), 0.0)


if __name__ == "__main__":
    unittest.main()