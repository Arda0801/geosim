import math

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
    Shipment,
    DemandProfile,
    District,
    Siege,
    Transaction,
    Order,
)
from sim.systems.accounting import (
    close_books,
    open_books,
)
from sim.systems.government import government_finance_phase
from sim.systems.hourly import hourly_phase
from sim.systems.market_clearing import market_clearing_phase
from sim.systems.markets import market_phase
from sim.systems.population import population_growth_phase
from sim.systems.production import production_phase
from sim.systems.trade import trade_phase
from sim.systems.siege import siege_phase
from sim.systems.events import apply_event
from sim.systems.finance import finance_phase
from sim.systems.transactions import execute_transaction

HOURS_PER_TICK = 24 * 7  # 1 tick = 1 week


class World:
    def __init__(self):
        self.hour_number = 0
        self.active_military_entities: set[str] = set()  # ids of units/sieges currently needing hourly resolution
        self.current_hour = 0
        self.tick_number = 0
        self.nations: dict[str, Nation] = {}
        self.companies: dict[str, Company] = {}
        self.banks: dict[str, Bank] = {}
        self.loans: dict[str, Loan] = {}
        self.events: list[Event] = []
        self.regions: dict[str, Region] = {}
        self.routes: dict[str, ShippingRoute] = {}
        self.markets: dict[str, Market] = {}
        self.day_number = 0
        self.commodities: dict[str, Commodity] = {}
        self.inventories: dict[tuple[str, str, str], Inventory] = {}
        self.production_facilities: dict[str, ProductionFacility] = {}
        self.shipments: dict[str, Shipment] = {}
        self.transactions: dict[str, Transaction] = {}
        self.demand_profiles: list[DemandProfile] = []
        self.districts: dict[str, District] = {}
        self.sieges: dict[str, Siege] = {}
        self.orders: dict[str, Order] = {}

    def add_market(self, market: Market):
        self.markets[market.id] = market

    def add_region(self, region: Region):
        self.regions[region.id] = region

    def add_district(self, district: District):
        if any(
            siege.status == "active" and siege.district_id == district.id
            for siege in self.sieges.values()
        ):
            district.contested = True
        self.districts[district.id] = district

    def add_route(self, route: ShippingRoute):
        self.routes[route.id] = route

    def add_nation(self, nation: Nation):
        self.nations[nation.id] = nation

    def add_company(self, company: Company):
        self.companies[company.id] = company

    def add_commodity(self, commodity):
        self.commodities[commodity.id] = commodity

    def add_production_facility(self, facility: ProductionFacility):
        self.production_facilities[facility.id] = facility

    def add_siege(self, siege: Siege):
        self.sieges[siege.id] = siege
        district = self.districts.get(siege.district_id)
        if district and siege.status == "active":
            district.contested = True

    def add_order(self, order: Order):
        self.orders[order.id] = order

    def add_inventory(
        self,
        owner_id: str,
        commodity_id: str,
        region_id: str,
        quantity: float,
        capacity: float = 100000,
    ):
        if not math.isfinite(quantity) or quantity < 0:
            raise ValueError("Inventory quantity must be finite and non-negative")
        if not math.isfinite(capacity) or capacity < 0:
            raise ValueError("Inventory capacity must be finite and non-negative")

        key = (owner_id, commodity_id, region_id)

        if key not in self.inventories:
            self.inventories[key] = Inventory(
                owner_id=owner_id,
                commodity_id=commodity_id,
                region_id=region_id,
                quantity=0.0,
                capacity=capacity,
            )

        inventory = self.inventories[key]

        if inventory.quantity + quantity > inventory.capacity:
            raise ValueError("Inventory capacity exceeded")

        inventory.quantity += quantity

    def add_bank(self, bank: Bank):
        self.banks[bank.id] = bank

    def add_loan(self, loan: Loan):
        self.loans[loan.id] = loan

    def add_transaction(self, transaction: Transaction):
        if transaction.id in self.transactions:
            raise ValueError(
                f"Transaction {transaction.id} already exists"
            )

        self.transactions[transaction.id] = transaction

    def execute_transaction(
        self,
        transaction_id: str,
        seller_id: str,
        buyer_id: str,
        commodity_id: str,
        quantity: float,
        price_per_unit: float,
        region_id: str,
    ) -> Transaction:
        return execute_transaction(
            self,
            transaction_id,
            seller_id,
            buyer_id,
            commodity_id,
            quantity,
            price_per_unit,
            region_id,
        )

    def add_demand_profile(self, profile: DemandProfile):
        self.demand_profiles.append(profile)

    def queue_event(self, event: Event):
        if any(queued.id == event.id for queued in self.events):
            raise ValueError(f"Event {event.id} already exists")
        self.events.append(event)

    def run_tick(self):
        self.tick_number += 1
        open_books(self)
        trade_phase(self)
        production_phase(self)
        market_clearing_phase(self)
        for _ in range(7):
            self.run_day()
        finance_phase(self)
        population_growth_phase(self)
        close_books(self)
        government_finance_phase(self)

    def run_hour(self):
        self.hour_number += 1
        self.current_hour += 1
        hourly_phase(self)

    def run_day(self):
        self.day_number += 1
        for _ in range(24):
            self.run_hour()
        siege_phase(self)
        market_phase(self)

    def remove_inventory(
        self,
        owner_id: str,
        commodity_id: str,
        region_id: str,
        quantity: float,
    ):
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        key = (owner_id, commodity_id, region_id)
        inventory = self.inventories.get(key)

        if inventory is None or inventory.quantity < quantity:
            raise ValueError("Insufficient inventory")

        inventory.quantity -= quantity

    def get_inventory_quantity(self, owner_id: str, commodity_id: str, region_id: str) -> float:
        """Exact quantity at one specific owner+region location."""
        inventory = self.inventories.get((owner_id, commodity_id, region_id))
        return inventory.quantity if inventory else 0.0

    def get_total_inventory_for_owner(self, owner_id: str, commodity_id: str) -> float:
        """Sum across every region this owner holds the commodity in."""
        return sum(
            inventory.quantity
            for (inventory_owner, inventory_commodity, _), inventory in self.inventories.items()
            if inventory_owner == owner_id and inventory_commodity == commodity_id
        )

    def get_region_inventory_quantity(self, region_id: str, commodity_id: str) -> float:
        """Sum all owners' stock of a commodity at one region."""
        return sum(
            inventory.quantity
            for inventory in self.get_inventories_in_region(region_id, commodity_id)
        )

    def get_region_storage_used(self, region_id: str) -> float:
        return sum(
            inv.quantity
            for (_, _, inventory_region), inv in self.inventories.items()
            if inventory_region == region_id
        )

    def get_inventories_in_region(
        self,
        region_id: str,
        commodity_id: str | None = None,
    ) -> list[Inventory]:
        inventories = [
            inventory
            for inventory in self.inventories.values()
            if inventory.region_id == region_id
        ]

        if commodity_id is not None:
            inventories = [
                inventory
                for inventory in inventories
                if inventory.commodity_id == commodity_id
            ]

        return inventories

    def get_dominant_controller(self, district_id: str) -> str | None:
        district = self.districts.get(district_id)
        if not district or not district.control:
            return None
        return max(district.control, key=lambda nation_id: district.control[nation_id])

    def apply_event(self, event: Event):
        apply_event(self, event)