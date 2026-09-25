import unittest

from sim.entities import Event, Market
from sim.systems.markets import market_phase
from tests.helpers import make_basic_world, make_production_world


class TestMarkets(unittest.TestCase):
    def test_regional_shock_only_affects_its_nation_market(self):
        w = make_basic_world()
        usa_market = Market(id="USA_MARKET", nation_id="USA", volatility_index=20.0)
        iran_market = Market(id="IRN_MARKET", nation_id="IRN", volatility_index=20.0)
        w.world.add_market(usa_market)
        w.world.add_market(iran_market)
        w.world.current_hour = 24
        w.world.events.append(
            Event(
                id="USA_SHOCK",
                event_type="missile_strike",
                timestamp_hours=0,
                target_id="PORT_USA",
                description="Regional shock",
                applied=True,
            )
        )

        market_phase(w.world)

        self.assertEqual(usa_market.volatility_index, 25.0)
        self.assertEqual(iran_market.volatility_index, 19.0)

    def test_applying_queued_event_twice_has_one_effect(self):
        w = make_production_world()
        event = Event(
            id="STRIKE_1",
            event_type="missile_strike",
            timestamp_hours=0,
            target_id="OILCO",
            description="Strike company capacity",
        )
        capacity_before = w.oil_co.production_capacity
        w.world.queue_event(event)
        with self.assertRaises(ValueError):
            w.world.queue_event(event)

        w.world.apply_event(event)
        w.world.apply_event(event)

        self.assertEqual(w.oil_co.production_capacity, capacity_before * 0.5)
        self.assertEqual(len(w.world.events), 1)


if __name__ == "__main__":
    unittest.main()