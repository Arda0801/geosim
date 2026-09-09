import unittest
from sim.entities import District, Siege
from tests.helpers import make_basic_world


class TestSiege(unittest.TestCase):
    def test_siege_erodes_control_gradually_without_flipping(self):
        world, usa, iran, port_usa, port_iran, crude, fuel = make_basic_world()

        district = District(
            id="HOUSTON_PORT",
            region_id="PORT_USA",
            name="Port District",
            control={"IRN": 0.9, "USA": 0.1},
            terrain_defense_multiplier=2.5,
        )
        world.add_district(district)

        siege = Siege(
            id="SIEGE_1",
            district_id="HOUSTON_PORT",
            attacker_nation_id="USA",
            defender_nation_id="IRN",
            attacker_committed_force=50.0,
            defender_morale=1.3,
        )
        world.add_siege(siege)

        for _ in range(30):
            world.run_day()

        irn_control = district.control["IRN"]

        # Should erode meaningfully, but not collapse outright, over 30 days
        self.assertLess(irn_control, 0.9)
        self.assertGreater(irn_control, 0.3)
        self.assertEqual(siege.status, "active")


if __name__ == "__main__":
    unittest.main()