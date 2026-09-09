import unittest
from tests.helpers import make_shipping_world


class TestShipping(unittest.TestCase):
    def test_goods_move_between_regions(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route = make_shipping_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)

        world.run_tick()

        self.assertEqual(world.get_inventory_quantity("PORT_IRN", "crude_oil"), 4000.0)
        self.assertEqual(world.get_inventory_quantity("PORT_USA", "crude_oil"), 1000.0)

    def test_blockade_stops_shipment_entirely(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route = make_shipping_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)
        world.run_tick()  # first shipment goes through

        route.status = "blockaded"
        route.risk_level = 1.0

        iran_before = world.get_inventory_quantity("PORT_IRN", "crude_oil")
        usa_before = world.get_inventory_quantity("PORT_USA", "crude_oil")

        world.run_tick()

        self.assertEqual(world.get_inventory_quantity("PORT_IRN", "crude_oil"), iran_before)
        self.assertEqual(world.get_inventory_quantity("PORT_USA", "crude_oil"), usa_before)


if __name__ == "__main__":
    unittest.main()