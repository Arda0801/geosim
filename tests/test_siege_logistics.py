import unittest
from sim.entities import District, Siege
from tests.helpers import make_full_industrial_world


class TestSiegeLogistics(unittest.TestCase):
    def test_siege_progresses_when_munitions_supplied(self):
        w = make_full_industrial_world()

        district = District(
            id="TESTDISTRICT", region_id="PORT_USA", name="Test District",
            control={"IRN": 0.9, "USA": 0.1},
        )
        w.world.add_district(district)

        w.world.add_inventory("PORT_USA", "munitions", 500)

        siege = Siege(
            id="SIEGE_1", district_id="TESTDISTRICT",
            attacker_nation_id="USA", defender_nation_id="IRN",
            attacker_committed_force=50.0,
        )
        w.world.add_siege(siege)

        for _ in range(10):
            w.world.run_day()

        self.assertLess(district.control["IRN"], 0.9)

    def test_siege_stalls_without_munitions(self):
        w = make_full_industrial_world()

        district = District(
            id="TESTDISTRICT", region_id="PORT_USA", name="Test District",
            control={"IRN": 0.9, "USA": 0.1},
        )
        w.world.add_district(district)

        # no munitions added at all

        siege = Siege(
            id="SIEGE_1", district_id="TESTDISTRICT",
            attacker_nation_id="USA", defender_nation_id="IRN",
            attacker_committed_force=50.0,
        )
        w.world.add_siege(siege)

        for _ in range(10):
            w.world.run_day()

        # with zero munitions, effective_attack should be 0, no progress made
        self.assertEqual(district.control["IRN"], 0.9)


if __name__ == "__main__":
    unittest.main()