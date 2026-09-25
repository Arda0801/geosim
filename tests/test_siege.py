import unittest
from sim.entities import District, Siege
from tests.helpers import make_basic_world


class TestSiege(unittest.TestCase):
    def test_siege_erodes_control_gradually_without_flipping(self):
        w = make_basic_world()

        district = District(
            id="HOUSTON_PORT",
            region_id="PORT_USA",
            name="Port District",
            control={"IRN": 0.9, "USA": 0.1},
            terrain_defense_multiplier=2.5,
        )
        w.world.add_district(district)

        w.world.add_inventory("PORT_USA", "munitions", "PORT_USA", 1000)

        siege = Siege(
            id="SIEGE_1",
            district_id="HOUSTON_PORT",
            attacker_nation_id="USA",
            defender_nation_id="IRN",
            attacker_committed_force=50.0,
            defender_morale=1.3,
        )
        w.world.add_siege(siege)

        for _ in range(30):
            w.world.run_day()

        irn_control = district.control["IRN"]

        # Should erode meaningfully, but not collapse outright, over 30 days
        self.assertLess(irn_control, 0.9)
        self.assertGreater(irn_control, 0.3)
        self.assertEqual(siege.status, "active")

    def test_simultaneous_sieges_preserve_control_and_contested_state(self):
        w = make_basic_world()
        district = District(
            id="MULTI_SIEGE_DISTRICT",
            region_id="PORT_USA",
            name="Contested District",
            control={"IRN": 0.005, "USA": 0.495, "CAN": 0.5},
        )
        w.world.add_district(district)
        sieges = [
            Siege(
                id="SIEGE_IRN",
                district_id=district.id,
                attacker_nation_id="USA",
                defender_nation_id="IRN",
                attacker_committed_force=100.0,
                munitions_consumed_per_day=0.0,
            ),
            Siege(
                id="SIEGE_CAN",
                district_id=district.id,
                attacker_nation_id="USA",
                defender_nation_id="CAN",
                attacker_committed_force=100.0,
                munitions_consumed_per_day=0.0,
            ),
        ]
        for siege in sieges:
            w.world.add_siege(siege)

        w.world.run_day()

        self.assertAlmostEqual(sum(district.control.values()), 1.0)
        self.assertTrue(district.contested)
        self.assertEqual(sieges[0].status, "resolved_attacker")
        self.assertEqual(sieges[1].status, "active")

    def test_district_contested_state_is_independent_of_registration_order(self):
        w = make_basic_world()
        siege = Siege(
            id="EARLY_SIEGE",
            district_id="LATE_DISTRICT",
            attacker_nation_id="USA",
            defender_nation_id="IRN",
            attacker_committed_force=10.0,
        )
        w.world.add_siege(siege)
        district = District(
            id="LATE_DISTRICT",
            region_id="PORT_USA",
            name="Late District",
        )

        w.world.add_district(district)

        self.assertTrue(district.contested)

        resolved_siege = Siege(
            id="RESOLVED_SIEGE",
            district_id="RESOLVED_DISTRICT",
            attacker_nation_id="USA",
            defender_nation_id="IRN",
            attacker_committed_force=10.0,
            status="resolved_attacker",
        )
        resolved_district = District(
            id="RESOLVED_DISTRICT",
            region_id="PORT_USA",
            name="Resolved District",
        )
        w.world.add_district(resolved_district)
        w.world.add_siege(resolved_siege)

        self.assertFalse(resolved_district.contested)


if __name__ == "__main__":
    unittest.main()