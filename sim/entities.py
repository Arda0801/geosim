from pydantic import BaseModel


class Nation(BaseModel):
    id: str
    name: str
    treasury: float
    gdp: float
    debt_total: float
    tax_rate: float  # e.g. 0.20 = 20%
    central_bank_rate: float  # e.g. 0.04 = 4%
    # Government finance (new)
    weekly_budget: float = 0.0  # baseline government spending per tick (military + social), placeholder
    bond_interest_rate: float = 0.00003  # weekly yield on government bonds, placeholder
    outstanding_bonds: float = 0.0  # total principal of bonds currently issued
    bonds_issued_last_tick: float = 0.0  # how much was borrowed this tick (for debugging/tests)
    interest_paid_last_tick: float = 0.0  # bond + legacy debt interest paid this tick
    tax_collected_last_tick: float = 0.0  # total tax revenue this tick (for debugging/tests)
    spending_last_tick: float = 0.0  # total spending this tick (for debugging/tests)

class Company(BaseModel):
    id: str
    name: str
    home_nation_id: str
    sector: str  # "energy", "shipping", "manufacturing", etc.
    cash: float
    production_capacity: float  # units/tick it can produce
    current_output: float = 0.0
    wage_cost_per_tick: float
    revenue_last_tick: float = 0.0
    input_costs_last_tick: float = 0.0
    wage_costs_last_tick: float = 0.0
    interest_paid_last_tick: float = 0.0
    principal_paid_last_tick: float = 0.0
    tax_paid_last_tick: float = 0.0
    profit_last_tick: float = 0.0
    total_revenue: float = 0.0
    total_profit: float = 0.0

class Bank(BaseModel):
    id: str
    name: str
    home_nation_id: str
    reserves: float
    loan_book_total: float = 0.0  # sum of all principal currently lent out

class Loan(BaseModel):
    id: str
    lender_id: str
    borrower_id: str
    principal: float
    remaining_balance: float
    interest_rate: float  # per-tick rate
    term_ticks: int  # how many ticks to pay it off
    ticks_elapsed: int = 0
    status: str = "active"

class Event(BaseModel):
    id: str
    event_type: str  # "missile_strike", "blockade", "ceasefire", etc.
    timestamp_hours: int  # hours since campaign start (June 13 2025, hour 0)
    target_id: str  # Region, Route, or Company id affected
    description: str
    applied: bool = False

class Region(BaseModel):
    id: str
    name: str
    owner_nation_id: str
    is_port: bool = False
    storage_capacity: float = 100_000.0
    population: float = 0.0
    growth_rate: float = 0.0  # per-tick fractional growth, e.g. 0.0004 for ~2%/year at weekly ticks

class District(BaseModel):
    id: str
    region_id: str
    name: str
    control: dict[str, float] = {}
    population: float = 0.0
    terrain_defense_multiplier: float = 1.0  # >1.0 favors defender (urban, mountainous)
    contested: bool = False  # true when actively being fought over

class Siege(BaseModel):
    id: str
    district_id: str
    attacker_nation_id: str
    defender_nation_id: str
    attacker_committed_force: float
    attacker_morale: float = 1.0
    defender_morale: float = 1.0
    status: str = "active"
    munitions_consumed_per_day: float = 5.0  # placeholder, tune later against real logistics data

class ShippingRoute(BaseModel):
    id: str
    origin_region_id: str
    destination_region_id: str
    capacity: float  # units/tick that can move
    base_cost: float  # cost per unit shipped, normal conditions
    risk_level: float = 0.0  # 0.0 = safe, 1.0 = fully blockaded
    status: str = "open"  # "open", "restricted", "blockaded"
    current_flow: float = 0.0
    current_cost: float = 0.0

class Market(BaseModel):
    id: str
    nation_id: str
    index_value: float = 1000.0  # like an S&P 500 equivalent, arbitrary start
    volatility_index: float = 10.0  # like VIX, arbitrary start

class Commodity(BaseModel):
    id: str
    name: str
    unit: str
    current_price: float = 10.0
    per_capita_daily_demand: float = 0.0  # units/person/day, 0 = not a population-demanded good
    # Market clearing fields (new)
    last_clearing_price: float = 0.0  # price from the most recent clearing
    last_volume_traded: float = 0.0  # total quantity matched in the most recent clearing
    last_buy_quantity: float = 0.0  # total buy order quantity in the most recent clearing
    last_sell_quantity: float = 0.0  # total sell order quantity in the most recent clearing

class DemandProfile(BaseModel):
    nation_id: str
    commodity_id: str

class Inventory(BaseModel):
    owner_id: str
    commodity_id: str
    region_id: str
    quantity: float = 0.0
    capacity: float = 100000.0

class ProductionFacility(BaseModel):
    id: str
    company_id: str
    region_id: str

    inputs: dict[str, float]
    outputs: dict[str, float]

    capacity: float
    efficiency: float = 1.0

    operational: bool = True

class Shipment(BaseModel):
    id: str
    route_id: str
    commodity_id: str
    quantity: float
    origin_region_id: str
    destination_region_id: str
    status: str = "in_transit"  # "in_transit", "delivered", "lost"

class Transaction(BaseModel):
    id: str
    seller_id: str
    buyer_id: str
    commodity_id: str
    quantity: float
    price_per_unit: float
    total_value: float
    timestamp_hours: int
    status: str = "completed"

class Order(BaseModel):
    id: str
    order_type: str  # "buy" or "sell"
    commodity_id: str
    owner_id: str  # company ID for sell orders, nation ID for population buy orders
    region_id: str  # where the goods are (sell) or where they're delivered (buy)
    quantity: float
    price: float
    tick_placed: int
    status: str = "open"
    filled_quantity: float = 0.0