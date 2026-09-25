def apply_event(world, event):
    world.events.append(event)

    if event.event_type == "missile_strike":
        company = world.companies.get(event.target_id)
        if company:
            company.production_capacity *= 0.5

    event.applied = True