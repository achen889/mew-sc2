 
from sharpy.plans.zerg import *      
from sharpy.managers.core.zone_manager import ZoneManager
from sc2.ids.unit_typeid import UnitTypeId

from .sharpy_exts import get_defense_position, MewDefensePosition
from ..queens_sc2.consts import QueenRoles
from ..queens_sc2.sharpy import QueensSc2Manager, SetQueensSc2Policy

class MikaQueenOverseer(QueensSc2Manager):
    def __init__(self,  zone_manager, **kwargs):
        super().__init__(**kwargs)
        #self.queens_manager = queens_manager
        self.zone_manager = zone_manager



    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        #print(format_table(knowledge))
        self.knowledge = knowledge
        #self.zone_manager = self.knowledge.zone_manager
        #await self.queens_manager.start(knowledge)
        #await self.zone_manager.start(knowledge)
        #self.queens_manager = self.knowledge.get_manager(QueensSc2Manager)
        #self.queens.debug = True

    @property
    def earlygame_creep_queens(self) -> dict:
        #self.zone_manager = self.knowledge.zone_manager

        my_natural_rally_point = get_defense_position(self.zone_manager.own_natural, MewDefensePosition.Entrance)
        return {
                "active": True,
                "distance_between_queen_tumors": 7,
                #"min_distance_between_existing_tumors": 3,
                "target_perc_coverage": 65,
                "first_tumor_position": my_natural_rally_point.towards(self.ai.game_info.map_center, 9),
                "priority": True,
                "prioritize_creep": lambda: True,
                "max": 1,
                "target_perc_coverage": 60,
                "defend_against_ground": True,
                "rally_point": my_natural_rally_point,  # Adjust this accordingly
                "priority_defence_list": {
                    UnitTypeId.ZERGLING,
                    UnitTypeId.MARINE,
                    UnitTypeId.BUNKER,
                    UnitTypeId.ZEALOT,
                    UnitTypeId.PROBE,
                    UnitTypeId.SCV,
                    UnitTypeId.DRONE,
                    UnitTypeId.PYLON,
                    UnitTypeId.PHOTONCANNON,
                    UnitTypeId.ORACLE,
                },
            }
    @property
    def midgame_creep_queens(self) -> dict:
        #self.zone_manager = self.knowledge.zone_manager
        my_natural_rally_point = get_defense_position(self.zone_manager.own_natural, MewDefensePosition.Entrance)
        return {
                "active": True,
                "distance_between_queen_tumors": 7,
                "min_distance_between_existing_tumors": 4,
                "target_perc_coverage": 75,
                "priority": True,
                "prioritize_creep": lambda: True,
                "max": 2,
                "defend_against_ground": False,
                "defend_against_air": True,
                "rally_point": my_natural_rally_point,  # Adjust this accordingly
                "priority_defence_list": {
                    #mid game units
                    UnitTypeId.BATTLECRUISER,
                    UnitTypeId.LIBERATOR,
                    UnitTypeId.LIBERATORAG,
                    UnitTypeId.VOIDRAY,
                },
            }
    @property
    def defense_queens(self) -> dict:
        #self.zone_manager = self.knowledge.zone_manager
        my_natural_rally_point = get_defense_position(self.zone_manager.own_natural, MewDefensePosition.Entrance)
        return {
            "attack_condition": lambda: self.ai.enemy_units.filter(
                lambda u: u.type_id == UnitTypeId.WIDOWMINEBURROWED
                    and u.distance_to(self.ai.enemy_start_locations[0]) > 50
                    and not self.queens.defence.enemy_air_threats
                    and not self.queens.defence.enemy_ground_threats)
                    or (
                        self.ai.structures(UnitTypeId.NYDUSCANAL)
                        and self.ai.units(UnitTypeId.QUEEN).amount > 25
                    ),
            "defend_against_ground": True,
            "defend_against_air": True,
            "priority_defence_list": {
                    UnitTypeId.ZERGLING,
                    UnitTypeId.MARINE,
                    UnitTypeId.ZEALOT,
                    UnitTypeId.PROBE,
                    UnitTypeId.SCV,
                    UnitTypeId.DRONE,
                    UnitTypeId.PYLON,
                    UnitTypeId.PHOTONCANNON,
                    UnitTypeId.SPINECRAWLER,
                    UnitTypeId.ORACLE,
                    UnitTypeId.MUTALISK,
                    UnitTypeId.OVERLORD,
                    UnitTypeId.BANSHEE,
                    UnitTypeId.VOIDRAY,
                    UnitTypeId.BATTLECRUISER,
                },
            "rally_point": my_natural_rally_point,
        }

    @property
    def nydus_queens(self) -> dict:
        return {
                    "active": True,
                    "max": 12,
                    "steal_from": {QueenRoles.Defence},
                }

    # @property
    # def early_game_queen_policy(self) -> dict:
    #     return {
    #         "creep_queens": {"active": False},
    #         "defence_queens": self.defense_queens,
    #         "creep_dropperlord_queens": {
    #             "active": True,
    #             "priority": True,
    #             "max": 1,
    #             "pass_own_threats": True,
    #             "target_expansions": [
    #                 el for el in self.zone_manager.expansion_zones[-6:-3]
    #             ],
    #         },
    #         "inject_queens": {"active": True},
    #         "nydus_queens": self.nydus_queens
    #     }
    @property
    def early_game_queen_policy(self) -> dict:
        return {
            "creep_queens": self.earlygame_creep_queens,
            "defence_queens": self.defense_queens,
            "creep_dropperlord_queens": {
                "active": False,
                "priority": False,
                "max": 1,
                "pass_own_threats": True,
                "target_expansions": [
                    el for el in self.zone_manager.expansion_zones[-6:-3]
                ],
            },
            "inject_queens": {"active": False},
            "nydus_queens": self.nydus_queens
        }

    @property
    def mid_game_queen_policy(self) -> dict:
        return {
            "creep_queens": self.midgame_creep_queens,
            "defence_queens": self.defense_queens,
            "creep_dropperlord_queens": {
                "active": True,
                "priority": True,
                "max": 2,
                "pass_own_threats": True,
                "priority_defence_list": set(),
                "target_expansions": [el for el in self.zone_manager.expansion_zones[-6:-3]],  # Adjust this accordingly
            },
            "inject_queens": {
                "active": True,
                "priority": False,
            },
            "nydus_queens": self.nydus_queens
        }

   
    async def update(self):
        await super().update()

        #self.ai.cache.


        

    async def post_update(self):
        await super().post_update()
        self.queens._draw_debug_info()
        #self.client.debug_text_2d(msg, Point2((0.1, 0.15)), None, 15)

class MikaSetQueensSc2Policy(ActBase):
    def __init__(self):
        super().__init__()
        self.early_game_done = False
        self.mid_game_done = False
        self.queen_policy = None
        self.policy_name = None
        self.mid_game_time = 60 * 5

    async def execute(self) -> bool:
        if not self.early_game_done:
            if self.ai.time < self.mid_game_time:
                self.queen_policy = MikaQueenOverseer.get_instance().early_game_queen_policy
                #print(f"\n{format_table(self.queen_policy)}")
                self.policy_name = f"Mika Early Game time: {self.ai.time} < {self.mid_game_time} s"

                self.early_game_done = True
        if not self.mid_game_done:
            if self.ai.time > self.mid_game_time:
                self.queen_policy = MikaQueenOverseer.get_instance().mid_game_queen_policy
                self.policy_name = f"Mika Mid Game time: {self.ai.time} > {self.mid_game_time} s"
                
                self.mid_game_done = True
        
        if self.queen_policy:
            MikaQueenOverseer.get_instance().set_new_policy(self.queen_policy)
            if self.policy_name:
                self.print(f"Mika Queen policy changed to {self.policy_name}")

            self.queen_policy = None
            self.policy_name = None
   
            return True