import random
import networkx as nx
from .data import TankWithAnimalsCondition, AnimalFilter, Requirements
from .data_loader import MEGAQUARIUM_DB


class SpeciesCompatibilityGraph:

    def __init__(self,species):
        self.species = species
        self._build()
    
    def _build(self):
        self.graph = nx.Graph()
        self.species_map = dict(list(map(lambda species: (species.gameId, species), self.species)))
        for species in self.species:
            self.graph.add_node(species.gameId)

        for species1 in self.species:
            for species2 in self.species:
                if species1.gameId == species2.gameId:
                    continue

                if species1.compatible_with([species2]):
                    self.graph.add_edge(species1.gameId, species2.gameId)

    def possible_tanks(self):
        for subg in nx.connected_components(self.graph):
            yield list(map(lambda n: self.species_map[n], subg))

    def most_diverse_tank(self):
        return max(map(lambda tank: len(tank),self.possibleTanks()))

    def get_compatible(self, species):
        for node in self.graph.neighbors(species.gameId):
            yield self.species_map[node]




    def filter_graph(self, filter_func):
        graph_filtered = self.graph.copy()
        species_map_filtered = {}
        for node in self.graph.nodes:
            if not filter_func(self.species_map[node]):
                graph_filtered.remove_node(node)
            else:
                species_map_filtered[node] = self.species_map[node]

        newG = SpeciesCompatibilityGraph([])
        newG.graph = graph_filtered
        newG.species_map = species_map_filtered
        return newG


ANIMAL_COMPATIBILITY_GRAPH = SpeciesCompatibilityGraph(MEGAQUARIUM_DB.get_animals())

def random_weighted_choice(choices):
    total = sum(map(lambda x: x[1], choices))
    weights = list(map(lambda x: x[1] / total, choices))
    options = list(map(lambda x: x[0], choices))
    return random.choices(options, weights=weights, k=1)[0] 


def _unique_count(iterator, toKey):
    results = {}
    for it in iterator:
        key = toKey(it)
        if not key in results:
            results[key] = [] 
        
        results[key].append(it)
    return results

def build_species_compatibility_graph(species):
    

    return 

def random_selection(values, probability=0.8):
    valueList = list(values)
    random.shuffle(valueList)
    while len(valueList) > 0:
        if random.random() < probability:
            yield valueList.pop(0)

def random_count(valueList, probability=0.8):
    for i in range(len(valueList)):
        if random.random() > probability:
            return i+1
    
    return len(valueList)

def random_species_tank(db,max_rank,MAX_SPECIES=4): 
    at_rank_animals = list(db.get_animals(lambda animal: animal.rank == max_rank))
    valid_animals = ANIMAL_COMPATIBILITY_GRAPH.filter_graph(lambda animal: animal.rank <= max_rank)
    random.shuffle(at_rank_animals)
    key_animal = at_rank_animals[0]

    tank_animals = [key_animal]
    compatible_valid_animals = valid_animals.get_compatible(key_animal)
    tank_animals += list(random_selection(compatible_valid_animals, probability=0.6))
    if len(tank_animals) > MAX_SPECIES:
        tank_animals = tank_animals[:4]


    tank_reqs = list(map(lambda t: (t,1), tank_animals))
    condition = TankWithAnimalsCondition(items=tank_reqs, rank=max_rank,filtered=False, compatGraph=[compatible_valid_animals])
    condition.heating = True
    condition.filtering = True
    return condition

def choose_num_distinct_species(compatibleAnimals, probability=0.6):
    tankOptions = []
    for tank in compatibleAnimals.possible_tanks():
        tankOptions.append(tank)

    if len(tankOptions) == 0:
        return 0
    random.shuffle(tankOptions)
    return random_count(tankOptions[0], probability=probability)

def random_condition_tank(db, max_rank):
    
    conditionTypes = [("genus", 1), ("eats", 1), ("shoaler", 1), ("any",1)]
    valid_animals = list(db.get_animals(lambda animal: animal.rank <= max_rank))

    condType = random_weighted_choice(conditionTypes)
    count = 1
    compatibleAnimals = None
    if condType == "genus":
        # pick a random genus from the valid animals
        validGenuses = _unique_count(valid_animals, lambda animal: animal.genus)
        genus = random.choice(list(validGenuses.keys()))
        compatibleAnimals = ANIMAL_COMPATIBILITY_GRAPH.filter_graph(lambda animal: animal.rank <= max_rank and animal.genus == genus)
        animalFilter = AnimalFilter(genus=genus)
    elif condType == "eats":
        validFood = _unique_count(valid_animals, lambda animal: animal.food)
        food = random.choice(list(validFood.keys()))
        compatibleAnimals = ANIMAL_COMPATIBILITY_GRAPH.filter_graph(lambda animal: animal.rank <= max_rank and animal.food == food)
        animalFilter = AnimalFilter(eats=food)
    elif condType == "any":
        animalFilter = AnimalFilter()
        compatibleAnimals = ANIMAL_COMPATIBILITY_GRAPH.filter_graph(lambda animal: animal.rank <= max_rank)
    elif condType == "shoaler":
        validShoalers= set(filter(lambda animal: Requirements.shoaler in animal.requirements, valid_animals))
        compatibleAnimals = ANIMAL_COMPATIBILITY_GRAPH.filter_graph(lambda animal: animal.rank <= max_rank and Requirements.shoaler in animal.requirements)
        animalFilter = AnimalFilter(shoaler=True)
    else:
        raise Exception(f"unknown condition type {condType}")

    numDistinctSpecies = choose_num_distinct_species(compatibleAnimals, probability=0.3)
    if numDistinctSpecies == 0:
        return None
    else:
        animalFilter.numSpecies = numDistinctSpecies
        valid_tanks = filter(lambda tank: len(tank) >= animalFilter.numSpecies, compatibleAnimals.possible_tanks())
        condition = TankWithAnimalsCondition(items=[(animalFilter, 1)], rank=max_rank, filtered=False, compatGraph=list(valid_tanks))
        condition.heating = True
        condition.filtering = True
        return condition



        
        




def random_tank(db,max_rank, weights={"species":1.0}):
    weights = [("species",1), ("condition",2)]
    random_tank_type = random_weighted_choice(weights)
    if random_tank_type == "species":
        tank = random_species_tank(db, max_rank)
    elif random_tank_type == "condition":
        tank = random_condition_tank(db, max_rank)
    else:
        raise ValueError("Unknown tank type selected") 

    if tank is None:
        return random_tank(db, max_rank, weights)
    else:
        return tank

def remove_redundant_tanks(tanks):
    def tank_always_satisfies(parentTank, childTank):
        return parentTank.trivially_satisfies(childTank)
    
    include = []
    for key1,tank1 in tanks.items():
        redundant = False
        for key2,tank2 in tanks.items():
            if key1 == key2:
                continue
            redundant |= tank_always_satisfies(tank2, tank1)

            if tank_always_satisfies(tank2, tank1):
                print(f"{key2} always satisfies {key1}")
        if not redundant:
            include.append((key1,tank1))

    return dict(include)

def randomly_merge_tanks(tanks,probability=0.8):
    def mutually_satisfiable(parentTank,childTank):
        pset = list(map(lambda xs: set(map(lambda x: x.gameId, xs)), parentTank.compatGraph))
        cset = list(map(lambda xs: set(map(lambda x: x.gameId, xs)), childTank.compatGraph))
        for cs in cset:
            found_subset = len(list(filter(lambda x:  cs.issubset(x), pset))) > 0
            if not found_subset:
                return False
        return True
    
   
    merged = []
    for key1,tank1 in tanks.items():
        merged_tank1 = tank1
        for key2,tank2 in tanks.items():
            if key1 == key2:
                continue

            if merged_tank1.has_mutually_valid_solution(tank2) and random.random() < probability:
                merged_tank1 = merged_tank1.merge(tank2)
        
        merged.append((merged_tank1.content_id(), merged_tank1))

    return dict(merged)
                




def generate_random_tank_set(db,min_rank,max_rank,tanks_per_rank):
    tankset = {}
    for i in range(min_rank,max_rank+1):
        for j in range(tanks_per_rank):
            tank = random_tank(db,i)
            tankset[tank.content_id()] = tank
    
    print(f"number generated tanks={len(tankset)}")
    tankset_v1 = remove_redundant_tanks(tankset)
    print(f"number non-redundant tanks={len(tankset_v1)}")
    tankset_v2 = randomly_merge_tanks(tankset_v1)
    print(f"number merged tanks={len(tankset_v2)}")
    return remove_redundant_tanks(tankset_v2)

    