from sim.entities import Nation, Company, Bank, Loan, Event, Region, ShippingRoute
usa = Nation(
    id="USA",
    name="United States",
    treasury=500_000,
    gdp=27_000_000,
    debt_total=34_000_000,
    tax_rate=0.20,
    central_bank_rate=0.045,
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

hormuz_route = ShippingRoute(
    id="R_HORMUZ",
    origin_region_id="PORT_IRN",
    destination_region_id="PORT_USA",
    capacity=1000,
    base_cost=5.0,
)

from sim.engine import World
from sim.entities import Event

world = World()
world.add_nation(usa)
world.add_nation(iran)
world.add_region(port_usa)
world.add_region(port_iran)
world.add_route(hormuz_route)
world.add_company(oil_co)
world.add_bank(first_bank)
world.add_loan(loan_1)

print("--- Before any ticks ---")
print(oil_co)

world.run_tick()
print("\n--- After tick 1 ---")
print(oil_co)
print(first_bank)
print(usa)

strike = Event(
    id="E1",
    event_type="missile_strike",
    timestamp_hours=world.current_hour + 10,
    target_id="OILCO",
    description="Refinery hit, capacity halved",
)
world.apply_event(strike)

print("\n--- After missile strike (instant, no tick) ---")
print(oil_co)

world.run_tick()
print("\n--- Route state after tick 2 ---")
print(hormuz_route)

# simulate a blockade event
hormuz_route.risk_level = 1.0
hormuz_route.status = "blockaded"
world.run_tick()
print("\n--- Route state after blockade ---")
print(hormuz_route)