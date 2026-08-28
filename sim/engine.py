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
    DemandProfile
)

from sim.systems.production import produce

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
        self.inventories: dict[tuple[str, str], Inventory] = {}
        self.production_facilities: dict[str, ProductionFacility] = {}
        self.shipments: dict[str, Shipment] = {}
        self.demand_profiles: list[DemandProfile] = []

    def add_market(self, market: Market):
        self.markets[market.id] = market

    def add_region(self, region: Region):
        self.regions[region.id] = region

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

    def _population_growth_phase(self):
        for region in self.regions.values():
            region.population *= (1 + region.growth_rate)

    def add_inventory(
        self,
        owner_id: str,
        commodity_id: str,
        quantity: float
    ):
        key = (owner_id, commodity_id)

        if key not in self.inventories:
            self.inventories[key] = Inventory(
                owner_id=owner_id,
                commodity_id=commodity_id,
                quantity=0.0
            )

        inventory = self.inventories[key]

        if inventory.quantity + quantity > inventory.capacity:
            raise ValueError(
                f"Inventory capacity exceeded for "
                f"{owner_id}/{commodity_id}"
            )

        inventory.quantity += quantity

    def add_bank(self, bank: Bank):
        self.banks[bank.id] = bank

    def add_loan(self, loan: Loan):
        self.loans[loan.id] = loan

    def add_demand_profile(self, profile: DemandProfile):
        self.demand_profiles.append(profile)

    def queue_event(self, event: Event):
        self.events.append(event)

    def run_tick(self):
        self.tick_number += 1

        self._production_phase()
        self._trade_phase()

        for _ in range(7):
            self.run_day()

        self._finance_phase()
        self._nation_phase()
        self._population_growth_phase()

    def run_hour(self):
        self.hour_number += 1
        self.current_hour += 1
        self._hourly_phase()

    def _hourly_phase(self):
        # Only entities actively engaged in movement/combat/siege get evaluated.
        # Empty for now — Phase 4 will populate active_military_entities and
        # resolve movement/combat here.
        for entity_id in self.active_military_entities:
            pass

    def run_day(self):
        self.day_number += 1
        for _ in range(24):
            self.run_hour()
        self._demand_and_pricing_phase()
        self._market_phase()

    def _market_phase(self):
        for market in self.markets.values():
            # crude sentiment proxy: recent blockades/strikes raise volatility
            recent_shock = any(
                e.timestamp_hours >= self.current_hour - 24 and not e.applied is False
                for e in self.events
            )
            if recent_shock:
                market.volatility_index += 5.0
                market.index_value *= 0.98  # 2% daily drop on shock days
            else:
                market.volatility_index = max(10.0, market.volatility_index * 0.95)  # decay toward baseline
                market.index_value *= 1.001  # small daily drift up, placeholder

    def remove_inventory(
        self,
        owner_id: str,
        commodity_id: str,
        quantity: float
    ):
        key = (owner_id, commodity_id)

        if key not in self.inventories:
            raise ValueError(
                f"No inventory exists for "
                f"{owner_id}/{commodity_id}"
            )

        inventory = self.inventories[key]

        if inventory.quantity < quantity:
            raise ValueError(
                f"Not enough {commodity_id} in inventory "
                f"for {owner_id}"
            )

        inventory.quantity -= quantity

    def get_inventory_quantity(
        self,
        owner_id: str,
        commodity_id: str
    ) -> float:

        key = (owner_id, commodity_id)

        if key not in self.inventories:
            return 0.0

        return self.inventories[key].quantity

    def _demand_and_pricing_phase(self):
        for profile in self.demand_profiles:
            commodity = self.commodities.get(profile.commodity_id)
            if not commodity:
                continue

            nation_regions = [
                r for r in self.regions.values()
                if r.owner_nation_id == profile.nation_id
            ]

            total_daily_demand = sum(
                r.population * commodity.per_capita_daily_demand
                for r in nation_regions
            )

            if total_daily_demand <= 0:
                continue

            total_available = sum(
                self.get_inventory_quantity(r.id, profile.commodity_id)
                for r in nation_regions
            )

            demand_met = min(total_daily_demand, total_available)
            remaining_to_consume = demand_met

            for region in nation_regions:
                if remaining_to_consume <= 0:
                    break
                available_here = self.get_inventory_quantity(region.id, profile.commodity_id)
                take = min(available_here, remaining_to_consume)
                if take > 0:
                    self.remove_inventory(region.id, profile.commodity_id, take)
                    remaining_to_consume -= take

            fulfillment_ratio = demand_met / total_daily_demand
            if fulfillment_ratio < 1.0:
                shortage = 1.0 - fulfillment_ratio
                commodity.current_price *= (1 + shortage * 0.1)
            else:
                commodity.current_price *= 0.999

    def get_region_storage_used(self, region_id: str) -> float:
        return sum(
            inv.quantity
            for (owner_id, _), inv in self.inventories.items()
            if owner_id == region_id
        )

    def _production_phase(self):

        for facility in self.production_facilities.values():

            produced = produce(
                facility,
                self
            )

            if produced > 0:

                company = self.companies.get(
                    facility.company_id
                )

                if company:
                    company.current_output = produced

    def _finance_phase(self):
        for loan in self.loans.values():
            if loan.status != "active":
                continue

            interest = loan.remaining_balance * loan.interest_rate
            principal_due = loan.principal / loan.term_ticks
            payment_due = interest + principal_due

            borrower = self.companies.get(loan.borrower_id)
            bank = self.banks.get(loan.lender_id)

            if borrower and borrower.cash >= payment_due:
                borrower.cash -= payment_due
                loan.remaining_balance -= principal_due
                if bank:
                    bank.reserves += payment_due
            elif borrower:
                # can't cover full payment — pay interest only if possible, else default risk
                if borrower.cash >= interest:
                    borrower.cash -= interest
                    if bank:
                        bank.reserves += interest
                # else: missed payment entirely — we'll add default handling later

            loan.ticks_elapsed += 1
            if loan.remaining_balance <= 0:
                loan.remaining_balance = 0.0
                loan.status = "paid_off"

    def _nation_phase(self):
        for nation in self.nations.values():
            nation_companies = [
                c for c in self.companies.values()
                if c.home_nation_id == nation.id
            ]
            for company in nation_companies:
                tax = company.cash * nation.tax_rate * 0.01  # small placeholder slice
                company.cash -= tax
                nation.treasury += tax

    def apply_event(self, event: Event):
        self.events.append(event)

        if event.event_type == "missile_strike":
            company = self.companies.get(event.target_id)
            if company:
                company.production_capacity *= 0.5  # halve capacity, placeholder severity

        event.applied = True

    def _trade_phase(self):
        for route in self.routes.values():
            if route.status == "blockaded":
                route.current_flow = 0.0
                route.current_cost = route.base_cost * 3
                continue

            effective_capacity = route.capacity * (1 - route.risk_level)
            effective_cost = route.base_cost * (1 + route.risk_level * 2)
            route.current_flow = effective_capacity
            route.current_cost = effective_cost

            # Try to ship whatever commodities are available at origin, up to capacity
            origin = route.origin_region_id
            destination = route.destination_region_id

            dest_region = self.regions.get(destination)
            if not dest_region:
                continue

            dest_used = self.get_region_storage_used(destination)
            dest_free = dest_region.storage_capacity - dest_used

            for (owner_id, commodity_id), inv in list(self.inventories.items()):
                if owner_id != origin:
                    continue

                shippable = min(inv.quantity, effective_capacity, dest_free)
                if shippable <= 0:
                    continue

                self.remove_inventory(origin, commodity_id, shippable)
                self.add_inventory(destination, commodity_id, shippable)

                dest_free -= shippable
                effective_capacity -= shippable

                if effective_capacity <= 0:
                    break