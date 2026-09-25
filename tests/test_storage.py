import unittest
from tests.helpers import make_production_world, make_shipping_world


class TestStorage(unittest.TestCase):
    def test_negative_inventory_is_rejected(self):
        w = make_shipping_world()

        with self.assertRaises(ValueError):
            w.world.add_inventory("PORT_IRN", "crude_oil", "PORT_IRN", -1.0)

        self.assertEqual(
            w.world.get_region_inventory_quantity("PORT_IRN", "crude_oil"),
            0.0,
        )

    def test_shipment_blocked_when_destination_storage_full(self):
        w = make_production_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", "PORT_IRN", 5000)
        w.refinery.operational = False  # keep crude from being consumed, so it piles up
        w.port_usa.storage_capacity = 500.0  # smaller than one shipment

        w.world.run_tick()  # first shipment, should be capped by storage, not route capacity

        usa_crude = w.world.get_region_inventory_quantity("PORT_USA", "crude_oil")
        self.assertLessEqual(usa_crude, 500.0)

    def test_no_shipment_when_storage_already_full(self):
        w = make_production_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", "PORT_IRN", 5000)
        w.refinery.operational = False
        w.port_usa.storage_capacity = 500.0

        w.world.run_tick()  # fills storage to capacity

        iran_before = w.world.get_region_inventory_quantity("PORT_IRN", "crude_oil")

        w.world.run_tick()  # storage already full, nothing more should ship

        iran_after = w.world.get_region_inventory_quantity("PORT_IRN", "crude_oil")
        self.assertEqual(iran_before, iran_after)


if __name__ == "__main__":
    unittest.main()