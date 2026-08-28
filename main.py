from sim.entities import (
    Nation,
    Company,
    Bank,
    Loan,
    Event,
    Region,
    ShippingRoute,
    Market,
    Commodity,
    Inventory,
    ProductionFacility,
    Shipment
)

from sim.systems.production import produce


usa = Nation(
    id="USA",
    name="United States",
    treasury=500_000,
    gdp=27_000_000,
    debt_total=34_000_000,
    tax_rate=0.20,
    central_bank_rate=0.045,
)

oil = Commodity(
    id="crude_oil",
    name="Crude Oil",
    unit="barrel"
)

steel = Commodity(
    id="steel",
    name="Steel",
    unit="tonne"
)

food = Commodity(
    id="food",
    name="Food",
    unit="tonne"
)

fuel = Commodity(
    id="fuel",
    name="Fuel",
    unit="barrel"
)

oil_co = Company(
    id="OILCO",
    name="Consolidated Oil",
    home_nation_id="USA",
    sector="energy",
    cash=10_000,
    production_capacity=1_000,
    wage_cost_per_tick=2_000,
)

first_bank = Bank(
    id="FIRSTBANK",
    name="First National Bank",
    home_nation_id="USA",
    reserves=50_000,
)

loan_1 = Loan(
    id="L1",
    lender_id="FIRSTBANK",
    borrower_id="OILCO",
    principal=20_000,
    remaining_balance=20_000,
    interest_rate=0.01,
    term_ticks=52,
)

refinery = ProductionFacility(
    id="REFINERY_01",
    company_id="OILCO",
    region_id="PORT_USA",

    inputs={
        "crude_oil": 1.0,
    },

    outputs={
        "fuel": 0.9,
    },

    capacity=1000,
)

iran = Nation(
    id="IRN",
    name="Iran",
    treasury=50_000,
    gdp=400_000,
    debt_total=10_000,
    tax_rate=0.15,
    central_bank_rate=0.23,
)

port_usa = Region(id="PORT_USA", name="Port of Houston", owner_nation_id="USA", is_port=True)
port_iran = Region(id="PORT_IRN", name="Port of Bandar Abbas", owner_nation_id="IRN", is_port=True)
usa_market = Market(id="NYSE", nation_id="USA")

hormuz_route = ShippingRoute(
    id="R_HORMUZ",
    origin_region_id="PORT_IRN",
    destination_region_id="PORT_USA",
    capacity=1000,
    base_cost=5.0,
)

from sim.engine import World

world = World()
world.add_nation(usa)
world.add_nation(iran)
world.add_region(port_usa)
world.add_region(port_iran)
world.add_route(hormuz_route)
world.add_company(oil_co)
world.add_bank(first_bank)
world.add_loan(loan_1)
world.add_market(usa_market)
world.add_commodity(oil)
world.add_commodity(fuel)
world.add_production_facility(refinery)
world.add_inventory("PORT_IRN", "crude_oil", 5000)

print("\n--- Before shipping tick ---")
print("Iran port crude:", world.get_inventory_quantity("PORT_IRN", "crude_oil"))
print("USA port crude:", world.get_inventory_quantity("PORT_USA", "crude_oil"))

world.run_tick()

print("\n--- After shipping tick ---")
print("Iran port crude:", world.get_inventory_quantity("PORT_IRN", "crude_oil"))
print("USA port crude:", world.get_inventory_quantity("PORT_USA", "crude_oil"))

hormuz_route.status = "blockaded"
hormuz_route.risk_level = 1.0

print("\n--- Before blockaded shipping tick ---")
print("Iran port crude:", world.get_inventory_quantity("PORT_IRN", "crude_oil"))
print("USA port crude:", world.get_inventory_quantity("PORT_USA", "crude_oil"))

world.run_tick()

print("\n--- After blockaded shipping tick (should be unchanged) ---")
print("Iran port crude:", world.get_inventory_quantity("PORT_IRN", "crude_oil"))
print("USA port crude:", world.get_inventory_quantity("PORT_USA", "crude_oil"))

hormuz_route.status = "open"
hormuz_route.risk_level = 0.0

world.run_tick()  # ship more crude in, unblockaded

print("\n--- Fuel produced from shipped crude ---")
print("PORT_USA crude:", world.get_inventory_quantity("PORT_USA", "crude_oil"))
print("PORT_USA fuel:", world.get_inventory_quantity("PORT_USA", "fuel"))