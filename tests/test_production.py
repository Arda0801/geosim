import unittest
from sim.entities import Company, DemandProfile
from tests.helpers import make_production_world
from sim.systems.production import production_phase


class TestProduction(unittest.TestCase):
    def test_refinery_converts_crude_to_fuel_and_sells_at_market_price(self):
        w = make_production_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", "PORT_IRN", 5000)
        w.port_usa.population = 1_000_000
        w.fuel.per_capita_daily_demand = 0.01
        w.world.add_demand_profile(DemandProfile(nation_id="USA", commodity_id="fuel"))

        w.world.run_tick()  # ship crude in (but too late for this tick's production)
        cash_before = w.oil_co.cash

        w.world.run_tick()  # now crude is available, refinery should produce and sell to demand

        self.assertGreater(w.oil_co.cash, cash_before)

    def test_refinery_offline_produces_nothing(self):
        w = make_production_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", "PORT_IRN", 5000)
        w.world.run_tick()
        w.world.run_tick()

        w.refinery.operational = False
        cash_before = w.oil_co.cash

        w.world.run_tick()

        self.assertLessEqual(w.oil_co.cash, cash_before)

    def test_input_supplier_is_paid_for_the_inventory_it_owns(self):
        w = make_production_world()
        supplier = Company(
            id="CRUDE_SUPPLIER",
            name="Crude Supplier",
            home_nation_id="IRN",
            sector="energy",
            cash=0.0,
            production_capacity=0.0,
            wage_cost_per_tick=0.0,
        )
        w.world.add_company(supplier)
        w.world.add_inventory(
            supplier.id,
            "crude_oil",
            "PORT_USA",
            1000.0,
        )

        production_phase(w.world)

        self.assertGreater(supplier.revenue_last_tick, 0.0)
        self.assertEqual(
            w.world.get_total_inventory_for_owner(supplier.id, "crude_oil"),
            0.0,
        )


if __name__ == "__main__":
    unittest.main()