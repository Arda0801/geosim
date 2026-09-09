from sim.entities import Nation, Region, Commodity, Company, Bank, Loan, ProductionFacility, ShippingRoute
from sim.engine import World


def make_basic_world():
    """A minimal world with USA, Iran, one port each, and core commodities."""
    world = World()

    usa = Nation(
        id="USA", name="United States",
        treasury=500_000, gdp=27_000_000, debt_total=34_000_000,
        tax_rate=0.20, central_bank_rate=0.045,
    )
    iran = Nation(
        id="IRN", name="Iran",
        treasury=50_000, gdp=400_000, debt_total=10_000,
        tax_rate=0.15, central_bank_rate=0.23,
    )
    world.add_nation(usa)
    world.add_nation(iran)

    port_usa = Region(id="PORT_USA", name="Port of Houston", owner_nation_id="USA", is_port=True)
    port_iran = Region(id="PORT_IRN", name="Port of Bandar Abbas", owner_nation_id="IRN", is_port=True)
    world.add_region(port_usa)
    world.add_region(port_iran)

    crude = Commodity(id="crude_oil", name="Crude Oil", unit="barrel")
    fuel = Commodity(id="fuel", name="Fuel", unit="barrel")
    world.add_commodity(crude)
    world.add_commodity(fuel)

    return world, usa, iran, port_usa, port_iran, crude, fuel


def make_shipping_world():
    """Basic world plus a Hormuz-style route between the two ports."""
    world, usa, iran, port_usa, port_iran, crude, fuel = make_basic_world()

    route = ShippingRoute(
        id="R_HORMUZ",
        origin_region_id="PORT_IRN",
        destination_region_id="PORT_USA",
        capacity=1000,
        base_cost=5.0,
    )
    world.add_route(route)

    return world, usa, iran, port_usa, port_iran, crude, fuel, route


def make_production_world():
    """Shipping world plus a refinery, company, bank, and loan at PORT_USA."""
    world, usa, iran, port_usa, port_iran, crude, fuel, route = make_shipping_world()

    oil_co = Company(
        id="OILCO", name="Consolidated Oil", home_nation_id="USA", sector="energy",
        cash=10_000, production_capacity=1_000, wage_cost_per_tick=2_000,
    )
    world.add_company(oil_co)

    bank = Bank(id="FIRSTBANK", name="First National Bank", home_nation_id="USA", reserves=50_000)
    world.add_bank(bank)

    loan = Loan(
        id="L1", lender_id="FIRSTBANK", borrower_id="OILCO",
        principal=20_000, remaining_balance=20_000, interest_rate=0.01, term_ticks=52,
    )
    world.add_loan(loan)

    refinery = ProductionFacility(
        id="REFINERY_01", company_id="OILCO", region_id="PORT_USA",
        inputs={"crude_oil": 1.0}, outputs={"fuel": 0.9}, capacity=1000,
    )
    world.add_production_facility(refinery)

    return world, usa, iran, port_usa, port_iran, crude, fuel, route, oil_co, bank, loan, refinery