from sim.engine import World
from sim.entities import Nation, Region, Commodity, Company, Bank, Loan


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