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
        if district:
            district.contested = True

    def add_order(self, order: Order):
        self.orders[order.id] = order

    def add_inventory(
        self,
        owner_id: str,
        commodity_id: str,
        region_id: str | float,
        quantity: float | None = None,
        capacity: float = 100000,
    ):
        if quantity is None:
            if not isinstance(region_id, (int, float)):
                raise TypeError("quantity is required when region_id is provided")
            quantity = float(region_id)
            inventory_region_id = owner_id
        else:
            if not isinstance(region_id, str):
                raise TypeError("region_id must be a string")
            inventory_region_id = region_id

        key = (owner_id, commodity_id, inventory_region_id)

        if key not in self.inventories:
            self.inventories[key] = Inventory(
                owner_id=owner_id,
                commodity_id=commodity_id,
                region_id=inventory_region_id,
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
        region_id: str | float,
        quantity: float | None = None,
    ):
        if quantity is None:
            if not isinstance(region_id, (int, float)):
                raise TypeError("quantity is required when region_id is provided")
            quantity = float(region_id)
            inventory_region_id = owner_id
        else:
            if not isinstance(region_id, str):
                raise TypeError("region_id must be a string")
            inventory_region_id = region_id

        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        remaining = quantity
        direct_key = (owner_id, commodity_id, inventory_region_id)
        direct_inventory = self.inventories.get(direct_key)

        if direct_inventory is not None:
            taken = min(direct_inventory.quantity, remaining)
            direct_inventory.quantity -= taken
            remaining -= taken

        if remaining > 0:
            # Some inventories are stored under the company owner, while region stock keeps the region as the location.
            for (inventory_owner, inventory_commodity, inventory_region), inventory in list(self.inventories.items()):
                if inventory_commodity != commodity_id or inventory.quantity <= 0:
                    continue
                if inventory_owner != owner_id and inventory_region != inventory_region_id:
                    continue

                taken = min(inventory.quantity, remaining)
                inventory.quantity -= taken
                remaining -= taken
                if remaining <= 0:
                    break

        if remaining > 0:
            raise ValueError("Insufficient inventory")

    def get_inventory_quantity(
        self,
        owner_id: str,
        commodity_id: str,
        region_id: str | None = None,
    ) -> float:
        if region_id is not None:
            inventory = self.inventories.get((owner_id, commodity_id, region_id))
            return inventory.quantity if inventory else 0.0

        return sum(
            inventory.quantity
            for (inventory_owner, inventory_commodity, inventory_region), inventory
            in self.inventories.items()
            if inventory_commodity == commodity_id
            and (
                inventory_region == owner_id
                or (owner_id in self.companies and inventory_owner == owner_id)
            )
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