import unittest
from sim.entities import DemandProfile, Order
from tests.helpers import make_production_world


class TestMarketClearing(unittest.TestCase):

    def test_sell_orders_generated_when_company_has_inventory(self):
        """After production, the company should have sell orders for its output."""
        w = make_production_world()
        w.world.add_inventory("PORT_IRN", "crude_oil", "PORT_IRN", 5000)
        w.world.run_tick()

        # After production, OILCO should have fuel in its own inventory
        fuel_in_company = w.world.get_total_inventory_for_owner("OILCO", "fuel")
        self.assertGreater(fuel_in_company, 0)

        # Run another tick to generate sell orders from that inventory
        from sim.systems.market_clearing import generate_sell_orders
        generate_sell_orders(w.world)

        sell_orders = [
            o for o in w.world.orders.values()
            if o.order_type == "sell" and o.commodity_id == "fuel"
        ]
        self.assertGreater(len(sell_orders), 0)
        self.assertEqual(sell_orders[0].owner_id, "OILCO")

    def test_buy_orders_generated_from_demand(self):
        """DemandProfile entries should generate buy orders."""
        w = make_production_world()
        w.port_usa.population = 100_000
        w.fuel.per_capita_daily_demand = 0.01
        w.world.add_demand_profile(
            DemandProfile(nation_id="USA", commodity_id="fuel")
        )

        from sim.systems.market_clearing import generate_buy_orders
        generate_buy_orders(w.world)

        buy_orders = [
            o for o in w.world.orders.values()
            if o.order_type == "buy" and o.commodity_id == "fuel"
        ]
        self.assertGreater(len(buy_orders), 0)
        # Weekly demand = 100,000 * 0.01 * 7 = 7,000
        self.assertAlmostEqual(buy_orders[0].quantity, 7000.0)

    def test_price_discovery_when_supply_exceeds_demand(self):
        """More supply than demand should push the price down."""
        w = make_production_world()
        w.crude.current_price = 10.0
        w.fuel.current_price = 20.0
        w.port_usa.population = 100  # tiny demand
        w.fuel.per_capita_daily_demand = 0.001  # 100 * 0.001 * 7 = 0.7/week
        w.world.add_demand_profile(
            DemandProfile(nation_id="USA", commodity_id="fuel")
        )
        w.world.add_inventory("PORT_USA", "crude_oil", "PORT_USA", 5000)

        price_before = w.fuel.current_price
        w.world.run_tick()

        # With massive oversupply, price should drop
        self.assertLess(w.fuel.current_price, price_before)

    def test_price_discovery_when_demand_exceeds_supply(self):
        """More demand than supply should push the price up."""
        w = make_production_world()
        w.crude.current_price = 10.0
        w.fuel.current_price = 20.0
        w.port_usa.population = 1_000_000  # huge demand
        w.fuel.per_capita_daily_demand = 0.01  # 1M * 0.01 * 7 = 70,000/week
        w.world.add_demand_profile(
            DemandProfile(nation_id="USA", commodity_id="fuel")
        )
        w.world.add_inventory("PORT_USA", "crude_oil", "PORT_USA", 5000)

        price_before = w.fuel.current_price
        w.world.run_tick()

        # With massive shortage, price should rise
        self.assertGreater(w.fuel.current_price, price_before)

    def test_trades_execute_and_inventory_transfers(self):
        """Matched orders should transfer inventory and record revenue."""
        w = make_production_world()
        w.crude.current_price = 10.0
        w.fuel.current_price = 20.0
        w.port_usa.population = 50_000
        w.fuel.per_capita_daily_demand = 0.01  # 50k * 0.01 * 7 = 3,500/week
        w.world.add_demand_profile(
            DemandProfile(nation_id="USA", commodity_id="fuel")
        )
        w.world.add_inventory("PORT_USA", "crude_oil", "PORT_USA", 5000)

        cash_before = w.oil_co.cash
        w.world.run_tick()

        # Company should have sold some fuel and earned revenue
        self.assertGreater(w.oil_co.cash, cash_before)
        # Fuel should no longer be in company inventory (consumed)
        company_fuel = w.world.get_total_inventory_for_owner("OILCO", "fuel")
        # Most should have been sold (refinery produces 900/week, demand is 3500)
        self.assertLess(company_fuel, 900)

    def test_volume_traded_recorded(self):
        """After clearing, commodity should record how much was traded."""
        w = make_production_world()
        w.crude.current_price = 10.0
        w.fuel.current_price = 20.0
        w.port_usa.population = 50_000
        w.fuel.per_capita_daily_demand = 0.01
        w.world.add_demand_profile(
            DemandProfile(nation_id="USA", commodity_id="fuel")
        )
        w.world.add_inventory("PORT_USA", "crude_oil", "PORT_USA", 5000)

        w.world.run_tick()

        # Volume traded should be recorded (limited by supply: 900 fuel/week)
        self.assertGreater(w.fuel.last_volume_traded, 0)
        print("\nOrders this tick:")
        for o in w.world.orders.values():
            print(o)
        print("Company fuel remaining:", w.world.get_total_inventory_for_owner("OILCO", "fuel"))
        print("oil_co.total_revenue:", w.oil_co.total_revenue)
        self.assertLessEqual(w.fuel.last_volume_traded, 900)

    def test_clearing_price_between_buy_and_sell_limits(self):
        """The clearing price should be between the highest buy and lowest sell."""
        w = make_production_world()
        w.crude.current_price = 10.0
        w.fuel.current_price = 20.0
        w.port_usa.population = 50_000
        w.fuel.per_capita_daily_demand = 0.01
        w.world.add_demand_profile(
            DemandProfile(nation_id="USA", commodity_id="fuel")
        )
        w.world.add_inventory("PORT_USA", "crude_oil", "PORT_USA", 5000)

        w.world.run_tick()

        # Clearing price should be recorded and reasonable
        self.assertGreater(w.fuel.last_clearing_price, 0)
        # Should be in a reasonable range (between 50% and 200% of starting price)
        self.assertGreater(w.fuel.last_clearing_price, 10.0)   # > 50% of 20
        self.assertLess(w.fuel.last_clearing_price, 40.0)      # < 200% of 20

    def test_previous_tick_orders_expire_without_opposite_side(self):
        w = make_production_world()
        stale_order = Order(
            id="OLD_BUY",
            order_type="buy",
            commodity_id="fuel",
            owner_id="USA",
            region_id="PORT_USA",
            quantity=100.0,
            price=20.0,
            tick_placed=0,
        )
        w.world.tick_number = 1
        w.world.add_order(stale_order)

        from sim.systems.market_clearing import clear_market
        clear_market(w.world)

        self.assertEqual(stale_order.status, "expired")
        self.assertEqual(w.fuel.last_buy_quantity, 0.0)

    def test_all_matched_orders_use_one_uniform_price(self):
        w = make_production_world()
        w.world.tick_number = 1
        w.world.add_inventory("OILCO", "fuel", "PORT_USA", 10.0)
        buy_orders = [
            Order(
                id="BUY_HIGH",
                order_type="buy",
                commodity_id="fuel",
                owner_id="USA",
                region_id="PORT_USA",
                quantity=5.0,
                price=20.0,
                tick_placed=1,
            ),
            Order(
                id="BUY_LOW",
                order_type="buy",
                commodity_id="fuel",
                owner_id="USA",
                region_id="PORT_USA",
                quantity=5.0,
                price=10.0,
                tick_placed=1,
            ),
        ]
        sell_order = Order(
            id="SELL",
            order_type="sell",
            commodity_id="fuel",
            owner_id="OILCO",
            region_id="PORT_USA",
            quantity=10.0,
            price=5.0,
            tick_placed=1,
        )
        for order in [*buy_orders, sell_order]:
            w.world.add_order(order)

        from sim.systems.market_clearing import clear_market
        clear_market(w.world)

        self.assertAlmostEqual(w.fuel.last_clearing_price, 7.5)
        self.assertAlmostEqual(w.oil_co.revenue_last_tick, 75.0)


if __name__ == "__main__":
    unittest.main()