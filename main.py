from sim.entities import (
    DemandProfile,
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

print("\n--- Storage Artifically Inflated ---")
port_usa.storage_capacity = 1200.0  # deliberately tight, to test the cap

print("\n--- Storage capacity test ---")
print("PORT_USA storage capacity:", port_usa.storage_capacity)
print("PORT_USA storage used:", world.get_region_storage_used("PORT_USA"))

world.run_tick()  # try to ship another 1000 crude in, should partially/fully block on capacity

print("\n--- After tick with tight storage cap ---")
print("Iran port crude:", world.get_inventory_quantity("PORT_IRN", "crude_oil"))
print("PORT_USA crude:", world.get_inventory_quantity("PORT_USA", "crude_oil"))
print("PORT_USA fuel:", world.get_inventory_quantity("PORT_USA", "fuel"))
print("PORT_USA storage used:", world.get_region_storage_used("PORT_USA"))

refinery.operational = False

print("\n--- Storage capacity test (refinery disabled) ---")
print("PORT_USA storage capacity:", port_usa.storage_capacity)
print("PORT_USA storage used:", world.get_region_storage_used("PORT_USA"))

world.run_tick()

print("\n--- After tick, refinery still offline ---")
print("Iran port crude:", world.get_inventory_quantity("PORT_IRN", "crude_oil"))
print("PORT_USA crude:", world.get_inventory_quantity("PORT_USA", "crude_oil"))
print("PORT_USA storage used:", world.get_region_storage_used("PORT_USA"))

refinery.operational = True

port_usa.population = 2_300_000  # rough Houston metro, placeholder
port_usa.growth_rate = 0.0004

fuel.per_capita_daily_demand = 0.0005  # tune later against real per-capita fuel consumption data

usa_fuel_demand = DemandProfile(nation_id="USA", commodity_id="fuel")
world.add_demand_profile(usa_fuel_demand)

print("\n--- Fuel price before demand test ---")
print("Fuel price:", fuel.current_price)
print("PORT_USA fuel:", world.get_inventory_quantity("PORT_USA", "fuel"))

world.run_tick()

print("\n--- Fuel price after one tick (7 days of demand) ---")
print("Fuel price:", fuel.current_price)
print("PORT_USA fuel:", world.get_inventory_quantity("PORT_USA", "fuel"))

usa_fuel_demand = DemandProfile(nation_id="USA", commodity_id="fuel")

world.run_tick()

print("\n--- Fuel price after scarcity tick ---")
print("Fuel price:", fuel.current_price)
print("PORT_USA fuel:", world.get_inventory_quantity("PORT_USA", "fuel"))

print("\n--- Population growth check ---")
print("PORT_USA population before:", port_usa.population)
world.run_tick()
print("PORT_USA population after:", port_usa.population)