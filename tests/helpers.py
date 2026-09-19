from types import SimpleNamespace

from sim.engine import World
from sim.entities import (
    Nation, Region, Commodity, Company, Bank, Loan,
    ProductionFacility, ShippingRoute,
)


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

    return SimpleNamespace(
        world=world, usa=usa, iran=iran,
        port_usa=port_usa, port_iran=port_iran,
        crude=crude, fuel=fuel,
    )


def make_shipping_world():
    """Basic world plus a Hormuz-style route between the two ports."""
    w = make_basic_world()

    route = ShippingRoute(
        id="R_HORMUZ",
        origin_region_id="PORT_IRN",
        destination_region_id="PORT_USA",
        capacity=1000,
        base_cost=5.0,
    )
    w.world.add_route(route)
    w.route = route

    return w


def make_production_world():
    """Shipping world plus a refinery, company, bank, and loan at PORT_USA."""
    w = make_shipping_world()

    oil_co = Company(
        id="OILCO", name="Consolidated Oil", home_nation_id="USA", sector="energy",
        cash=10_000, production_capacity=1_000, wage_cost_per_tick=2_000,
    )
    w.world.add_company(oil_co)

    bank = Bank(id="FIRSTBANK", name="First National Bank", home_nation_id="USA", reserves=50_000)
    w.world.add_bank(bank)

    loan = Loan(
        id="L1", lender_id="FIRSTBANK", borrower_id="OILCO",
        principal=20_000, remaining_balance=20_000, interest_rate=0.01, term_ticks=52,
    )
    w.world.add_loan(loan)

    refinery = ProductionFacility(
        id="REFINERY_01", company_id="OILCO", region_id="PORT_USA",
        inputs={"crude_oil": 1.0}, outputs={"fuel": 0.9}, capacity=1000,
    )
    w.world.add_production_facility(refinery)

    w.oil_co = oil_co
    w.bank = bank
    w.loan = loan
    w.refinery = refinery

    return w


def make_multi_chain_world():
    """Production world plus a steel mill (consumes fuel) and food production."""
    w = make_production_world()

    steel = Commodity(id="steel", name="Steel", unit="tonne")
    food = Commodity(id="food", name="Food", unit="tonne")
    w.world.add_commodity(steel)
    w.world.add_commodity(food)

    steel_co = Company(
        id="STEELCO", name="American Steel", home_nation_id="USA", sector="manufacturing",
        cash=15_000, production_capacity=500, wage_cost_per_tick=3_000,
    )
    w.world.add_company(steel_co)

    steel_mill = ProductionFacility(
        id="STEELMILL_01", company_id="STEELCO", region_id="PORT_USA",
        inputs={"fuel": 1.0}, outputs={"steel": 0.7}, capacity=500,
    )
    w.world.add_production_facility(steel_mill)

    farm_co = Company(
        id="FARMCO", name="Heartland Foods", home_nation_id="USA", sector="agriculture",
        cash=8_000, production_capacity=800, wage_cost_per_tick=1_500,
    )
    w.world.add_company(farm_co)

    farm = ProductionFacility(
        id="FARM_01", company_id="FARMCO", region_id="PORT_USA",
        inputs={}, outputs={"food": 1.0}, capacity=800,
    )
    w.world.add_production_facility(farm)

    w.steel = steel
    w.food = food
    w.steel_co = steel_co
    w.steel_mill = steel_mill
    w.farm_co = farm_co
    w.farm = farm

    return w


def make_full_industrial_world():
    """Multi-chain world plus a munitions plant requiring steel AND fuel."""
    w = make_multi_chain_world()

    munitions = Commodity(id="munitions", name="Munitions", unit="crate")
    w.world.add_commodity(munitions)

    defense_co = Company(
        id="DEFENSECO", name="Patriot Defense Systems", home_nation_id="USA", sector="defense",
        cash=20_000, production_capacity=200, wage_cost_per_tick=4_000,
    )
    w.world.add_company(defense_co)

    munitions_plant = ProductionFacility(
        id="MUNITIONS_01", company_id="DEFENSECO", region_id="PORT_USA",
        inputs={"steel": 2.0, "fuel": 1.0},
        outputs={"munitions": 0.5},
        capacity=200,
    )
    w.world.add_production_facility(munitions_plant)

    w.munitions = munitions
    w.defense_co = defense_co
    w.munitions_plant = munitions_plant

    return w