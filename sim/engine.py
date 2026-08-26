from sim.entities import Nation, Company, Bank, Loan, Event, Region, ShippingRoute

HOURS_PER_TICK = 24 * 7  # 1 tick = 1 week


class World:
    def __init__(self):
        self.current_hour = 0
        self.tick_number = 0
        self.nations: dict[str, Nation] = {}
        self.companies: dict[str, Company] = {}
        self.banks: dict[str, Bank] = {}
        self.loans: dict[str, Loan] = {}
        self.events: list[Event] = []
        self.regions: dict[str, Region] = {}
        self.routes: dict[str, ShippingRoute] = {}

    def add_region(self, region: Region):
        self.regions[region.id] = region

    def add_route(self, route: ShippingRoute):
        self.routes[route.id] = route

    def add_nation(self, nation: Nation):
        self.nations[nation.id] = nation

    def add_company(self, company: Company):
        self.companies[company.id] = company

    def add_bank(self, bank: Bank):
        self.banks[bank.id] = bank

    def add_loan(self, loan: Loan):
        self.loans[loan.id] = loan

    def queue_event(self, event: Event):
        self.events.append(event)

    def run_tick(self):
        self.tick_number += 1
        self.current_hour += HOURS_PER_TICK

        self._production_phase()
        self._trade_phase()
        self._finance_phase()
        self._nation_phase()

    def _production_phase(self):
        for company in self.companies.values():
            company.current_output = company.production_capacity
            revenue = company.current_output * 50  # placeholder price per unit
            company.cash += revenue
            company.cash -= company.wage_cost_per_tick

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
                route.current_cost = route.base_cost * 3  # blockade risk premium, placeholder
                continue
            effective_capacity = route.capacity * (1 - route.risk_level)
            effective_cost = route.base_cost * (1 + route.risk_level * 2)
            route.current_flow = effective_capacity
            route.current_cost = effective_cost