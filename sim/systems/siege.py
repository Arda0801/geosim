def siege_phase(world):
    for siege in world.sieges.values():
        if siege.status != "active":
            continue

        district = world.districts.get(siege.district_id)
        if not district:
            continue

        attacker_regions = [
            r for r in world.regions.values()
            if r.owner_nation_id == siege.attacker_nation_id
        ]
        munitions_available = sum(
            inv.quantity
            for r in attacker_regions
            for inv in world.get_inventories_in_region(r.id, "munitions")
        )

        munitions_needed = siege.munitions_consumed_per_day
        supply_ratio = min(1.0, munitions_available / munitions_needed) if munitions_needed > 0 else 1.0

        remaining_to_consume = min(munitions_needed, munitions_available)
        for region in attacker_regions:
            if remaining_to_consume <= 0:
                break
            for inv in world.get_inventories_in_region(region.id, "munitions"):
                if remaining_to_consume <= 0:
                    break
                take = min(inv.quantity, remaining_to_consume)
                if take > 0:
                    world.remove_inventory(inv.owner_id, "munitions", region.id, take)
                    remaining_to_consume -= take

        defender_control = district.control.get(siege.defender_nation_id, 0.0)
        attacker_control = district.control.get(siege.attacker_nation_id, 0.0)

        effective_attack = (
            siege.attacker_committed_force
            * siege.attacker_morale
            * supply_ratio
        )
        effective_defense = (
            defender_control
            * district.terrain_defense_multiplier
            * siege.defender_morale
            * 100
        )

        if effective_attack <= 0:
            continue

        shift = min(
            0.02,
            effective_attack / (effective_attack + effective_defense) * 0.05,
            defender_control,
        )

        district.control[siege.attacker_nation_id] = attacker_control + shift
        district.control[siege.defender_nation_id] = max(0.0, defender_control - shift)

        if district.control[siege.defender_nation_id] <= 0.01:
            siege.status = "resolved_attacker"
            district.contested = any(
                other.status == "active" and other.district_id == district.id
                for other in world.sieges.values()
            )