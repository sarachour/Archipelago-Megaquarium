import random
from .data import TankWithAnimalsCondition, AnimalFilter

def random_weighted_choice(choices):
    total = sum(map(lambda x: x[1], choices))
    weights = list(map(lambda x: x[1] / total, choices))
    options = list(map(lambda x: x[0], choices))
    return random.choices(options, weights=weights, k=1)[0] 


def random_species_tank(db,max_rank): 
    at_rank_animals = list(db.get_animals(lambda animal: animal.rank == max_rank))
    valid_animals = list(db.get_animals(lambda animal: animal.rank <= max_rank))
    random.shuffle(at_rank_animals)
    random.shuffle(valid_animals)

    key_animal = at_rank_animals[0]
    tank_animals = [key_animal]
    total_species = 2 
    for animal in valid_animals[1:]:
        if len(tank_animals) >= total_species:
            break
        if animal.compatible_with(tank_animals) and not animal in tank_animals:
            tank_animals.append(animal)

    tank_reqs = list(map(lambda t: (t,1), tank_animals))
    condition = TankWithAnimalsCondition(items=tank_reqs, filtered=False)
    return condition


def random_condition_tank(db, max_rank):
    conditionTypes = [("genus", 1), ("eats", 1), ("shoaler", 1), ("any",1)]
    valid_animals = list(db.get_animals(lambda animal: animal.rank <= max_rank))

    condType = random_weighted_choice(conditionTypes)
    if condType == "genus":
        # pick a random genus from the valid animals
        validGenuses = set(map(lambda animal: animal.genus, valid_animals))
        genus = random.choice(list(validGenuses))
        animalFilter = AnimalFilter(genus=genus)
    elif condType == "eats":
        validFood = set(map(lambda animal: animal.food, valid_animals))
        food = random.choice(list(validFood))
        animalFilter = AnimalFilter(eats=food)
    elif condType == "any":
        animalFilter = AnimalFilter(numSpecies=1)
    elif condType == "shoaler":
        animalFilter = AnimalFilter(shoaler=True, numSpecies=2)

    condition = TankWithAnimalsCondition(items=[(animalFilter, 1)], filtered=False)
    return condition



        
        




def random_tank(db,max_rank, weights={"species":1.0}):
    weights = [("species",1), ("condition",2)]
    random_tank_type = random_weighted_choice(weights)
    if random_tank_type == "species":
        return random_species_tank(db, max_rank)
    elif random_tank_type == "condition":
        return random_condition_tank(db, max_rank)
    else:
        raise ValueError("Unknown tank type selected") 