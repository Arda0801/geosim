import unittest
from tests.helpers import make_shipping_world


class TestShipping(unittest.TestCase):
    def test_goods_move_between_regions(self):
        w = make_shipping_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", 5000)

        w.world.run_tick()

        self.assertEqual(w.world.get_inventory_quantity("PORT_IRN", "crude_oil"), 4000.0)
        self.assertEqual(w.world.get_inventory_quantity("PORT_USA", "crude_oil"), 1000.0)

    def test_blockade_stops_shipment_entirely(self):
        w = make_shipping_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", 5000)
        w.world.run_tick()  # first shipment goes through

        w.route.status = "blockaded"
        w.route.risk_level = 1.0

        iran_before = w.world.get_inventory_quantity("PORT_IRN", "crude_oil")
        usa_before = w.world.get_inventory_quantity("PORT_USA", "crude_oil")

        w.world.run_tick()

        self.assertEqual(w.world.get_inventory_quantity("PORT_IRN", "crude_oil"), iran_before)
        self.assertEqual(w.world.get_inventory_quantity("PORT_USA", "crude_oil"), usa_before)


if __name__ == "__main__":
    unittest.main()