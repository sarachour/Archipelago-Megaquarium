import random
from .data import TankWithAnimalsCondition

def random_tank(db,max_rank): 
    at_rank_animals = list(db.get_animals(lambda animal: animal.rank == max_rank))
    valid_animals = list(db.get_animals(lambda animal: animal.rank <= max_rank))
    random.shuffle(at_rank_animals)
    random.shuffle(valid_animals)

    total_species = random.choice([1,2,3,4]) 
    key_animal = at_rank_animals[0]
    tank_animals = [(key_animal,1)]
    for animal in valid_animals[1:]:
        if len(tank_animals) >= total_species:
            break
        
        if animal.compatible_with(map(lambda x: x[0], tank_animals)):
            tank_animals.append((animal,1))

    condition = TankWithAnimalsCondition(items=tank_animals, filtered=False)
    return condition



