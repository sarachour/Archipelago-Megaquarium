"""
Option definitions for Pokemon Emerald
"""
from dataclasses import dataclass

from Options import (Choice, DeathLink, DefaultOnToggle, OptionSet, NamedRange, Range, Toggle, FreeText,
                     PerGameCommonOptions, OptionGroup, StartInventory)





class Goal(Choice):
    """
    Determines what your goal is to consider the game beaten.

    - Max Rank: Reach the maximum rank (default is 6) 
    """
    display_name = "Goal"
    default = 0
    option_maxrank = 0


class StartRank(Range):
    """
    After it has been decided that a move will not be forced to match types, sets the probability that a learned move will be forced to be the Normal type.

    If a move is not forced to be Normal, it will be completely random.
    """
    display_name = "Start Rank"
    range_start = 1
    range_end = 12
    default = 1

class EndRank(Range):
    display_name = "Ending (Win) Rank"
    range_start = 1
    range_end = 12
    default = 6



@dataclass
class MegaquariumOptions(PerGameCommonOptions):
    goal: Goal
    start_rank: StartRank
    end_rank: EndRank


OPTION_GROUPS = [OptionGroup("Blacklisted Fish", [], True)]

