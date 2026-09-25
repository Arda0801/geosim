def population_growth_phase(world):
    for region in world.regions.values():
        region.population *= (1 + region.growth_rate)