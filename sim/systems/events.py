def apply_event(world, event):
    existing = next((queued for queued in world.events if queued.id == event.id), None)
    if existing is not None and existing is not event:
        raise ValueError(f"Event {event.id} already exists")

    if event.applied:
        if existing is None:
            world.events.append(event)
        return

    if existing is None:
        world.events.append(event)

    if event.event_type == "missile_strike":
        company = world.companies.get(event.target_id)
        if company:
            company.production_capacity *= 0.5

    event.applied = True