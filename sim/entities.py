from pydantic import BaseModel


class Nation(BaseModel):
    id: str
    name: str
    treasury: float
    gdp: float
    debt_total: float
    tax_rate: float  # e.g. 0.20 = 20%
    central_bank_rate: float  # e.g. 0.04 = 4%

class Company(BaseModel):
    id: str
    name: str
    home_nation_id: str
    sector: str  # "energy", "shipping", "manufacturing", etc.
    cash: float
    production_capacity: float  # units/tick it can produce
    current_output: float = 0.0
    wage_cost_per_tick: float

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

class Inventory(BaseModel):
    owner_id: str
    commodity_id: str
    quantity: float = 0.0
    capacity: float = float("inf")

class ProductionFacility(BaseModel):
    id: str
    company_id: str
    region_id: str

    inputs: dict[str, float]
    outputs: dict[str, float]

    capacity: float
    efficiency: float = 1.0

    operational: bool = True