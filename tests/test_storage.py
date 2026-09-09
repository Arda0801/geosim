import unittest
from tests.helpers import make_production_world


class TestStorage(unittest.TestCase):
    def test_shipment_blocked_when_destination_storage_full(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery = make_production_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)
        refinery.operational = False  # keep crude from being consumed, so it piles up
        port_usa.storage_capacity = 500.0  # smaller than one shipment

        world.run_tick()  # first shipment, should be capped by storage, not route capacity

        usa_crude = world.get_inventory_quantity("PORT_USA", "crude_oil")
        self.assertLessEqual(usa_crude, 500.0)

    def test_no_shipment_when_storage_already_full(self):
        world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery = make_production_world()
        world.add_inventory("PORT_IRN", "crude_oil", 5000)
        refinery.operational = False
        port_usa.storage_capacity = 500.0

        world.run_tick()  # fills storage to capacity

        iran_before = world.get_inventory_quantity("PORT_IRN", "crude_oil")

        world.run_tick()  # storage already full, nothing more should ship

        iran_after = world.get_inventory_quantity("PORT_IRN", "crude_oil")
        self.assertEqual(iran_before, iran_after)


if __name__ == "__main__":
    unittest.main()