from typing import List, Optional, Union, Set, Dict

from sc2.position import Point2, Point3, Pointlike
from sc2.ids.unit_typeid import UnitTypeId
from sharpy.general.zone import Zone
from sharpy.combat import Action
from sc2.unit import Unit
from sc2.units import Units
from sharpy.constants import Constants
from sharpy.managers.core import *

from sharpy.interfaces.combat_manager import MoveType
from sharpy.combat.combat_units import CombatUnits
from sharpy.combat.group_combat_manager import GroupCombatManager

from sharpy.managers.extensions import DataManager, BuildDetector, GameAnalyzer, HeatMapManager
from sharpy.managers.core.manager_base import ManagerBase
from sharpy.managers.extensions import BuildDetector, GameAnalyzer
from sharpy.interfaces import IEnemyUnitsManager
from sharpy.general.extended_power import ExtendedPower

from .mew_log import *
from .mew_expand import create_new_expansion_base, SmartExpand, ExpansionBase
from .nydus_solver import NydusSolver

from sharpy.tools import IntervalFunc
import numpy as np

def draw_text_on_world(ai, pos: Point2, text: str, draw_color=(255, 102, 255), font_size=14) -> None:
    z_height: float = ai.get_terrain_z_height(pos)
    ai.client.debug_text_world(
        text,
        Point3((pos.x, pos.y, z_height)),
        color=draw_color,
        size=font_size,
    )

class SingletonManager(ManagerBase):
    Instance = None
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)

    @classmethod
    def get_instance(cls, *arg, **kwarg):
        if not cls.Instance:
             cls.Instance = cls(*arg, **kwarg)
        return cls.Instance 

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.knowledge = knowledge
        #print(format_table(knowledge))

    async def update(self):
        super().update()
        pass

    async def post_update(self):
        super().post_update()
        pass

from enum import Enum, auto

class PowerTypeId(Enum):
    POWER = 0,
    AIR_PRESENCE = 1,
    GROUND_PRESENCE = 2,
    AIR_POWER = 3,
    GROUND_POWER = 4,
    MELEE_POWER = 5,
    SURROUND_POWER = 6,
    SIEGE_POWER = 7,
    DETECTORS = 8,
    STEALTH_POWER=9,
    NUM_TYPES =auto(),
    INVALID = -1

class PowerValues:
    def __init__(self, extended_power : ExtendedPower = None):
        self._values = {}
        self.total_power = 0
        self._update_from(extended_power)
        self.debug = False

        
        #print(get_class_attributes(self))
    
    def __getitem__(self, power_type : PowerTypeId):
        name = power_type.name.lower()
        return self._values.get(name, 0)

    def __setitem__(self, power_type: PowerTypeId, value):
        self._values[key] = value

    def _update_from(self, extended_power: ExtendedPower):
        if extended_power:
            self._values.update(extended_power.__dict__)
            self.total_power = self._values['power']
            # for k,v in self._values.items():
            #     print(f"\n ~ | {type(k)}={k}: {type(v)}={v} ")

    def _calc_relative_power(self, power_types: Union[PowerTypeId, List[PowerTypeId]]):
        if self.debug: print(f"{self}::_calc_relative_power : power_types: {type(power_types)} = {power_types}")
        if isinstance(power_types, list):
            # If power_types is a list, calculate relative power for each power type in the list
            relative_powers = []
            for power_type in power_types:
                relative_power_value = self._values.get(power_type, 0) / (1.0 + self.total_power)
                if self.debug: print(f"{self}::_calc_relative_power : relative_power_value: {type(relative_power_value)} = {relative_power_value}")
                relative_powers.append(relative_power_value)
            if self.debug: print(f"{self}::_calc_relative_power : relative_powers: {type(relative_powers)} = {relative_powers}")
            return relative_powers
        else:
            # If power_types is a single PowerTypeId, calculate relative power for that power type
            relative_power_value = self._values.get(power_types, 0) / (1.0 + self.total_power)
            if self.debug: print(f"{self}::_calc_relative_power : relative_power_value: {type(relative_power_value)} = {relative_power_value}")
            return relative_power_value

from .unit_state import UnitState

class ArmyManager(SingletonManager):
    def __init__(self):
        self.supply_unit_types = [UnitTypeId.OVERLORD, UnitTypeId.SUPPLYDEPOT, UnitTypeId.PYLON]
        #self.townhall_unit_types = [UnitTypeId.COMMANDCENTER, UnitTypeId.NEXUS, UnitTypeId.HATCHERY]
        self.worker_type = UnitTypeId.DRONE
        self.unit_types = [] #unit types to consider frontline army

        self.worker_count = 0
        self.army = {}
        self.last_attacker_tags = {}
        self.army_supply = {}
        self.my_total_power = PowerValues()

        self.enemy_worker_count = 0
        self.enemy_army = {}
        self.enemy_army_supply = {}
        self.enemy_total_power= PowerValues()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        #print(format_table(knowledge))
        self.unit_values = knowledge.unit_values
        self.enemy_units_manager = knowledge.get_manager(IEnemyUnitsManager)
        #self.create_expansion_base(self.zone_manager.own_main_zone)
        self.update_enemy_army_power()
        self.update_army_power()

    async def update(self):
        super().update()

        self.update_enemy_army_power()
        self.update_army_power()
        self.update_army_attacker_tags()

        self._update_enemy_unit_states()
        

        #can compare or collect metrics here

    async def post_update(self):
        super().post_update()

        self.render_debug()

    def render_debug(self):
        worker_str = f"Workers: {self.worker_count} "
        larva_str = f"Larva: { len(self.cache.own(UnitTypeId.LARVA))}"

        fancy_army = ""
        for key,value, in self.army_supply.items():
            fancy_army += f'\n ~ | {key} x {value}\n'
        #format_table(self.army_supply)
        army_str = f"===Army==={fancy_army}"
        #mineral_str = f"Minerals: {self.mineral_amount}+{self.mineral_rate}/s" #ansi_color_str(f"Minerals: {self.mineral_amount}+{self.mineral_rate}/s", fg='white',bg='cyan')
        #gas_str = f"Vespene: {self.gas_amount}+{self.gas_rate}/s" #ansi_color_str(f"Vespene: {self.gas_amount}+{self.gas_rate}/s", fg='white',bg='green')

        msg = f"===Self===\
            \n ~ | {worker_str} \
            \n ~ | {larva_str} \
            \n ~ | {army_str}"

        self.client.debug_text_2d(msg, Point2((0.1, 0.15)), None, 15)
        
        enemy_worker_str = f"Workers: {self.enemy_worker_count} "

        fancy_enemy_army = ""
        for key,value, in self.enemy_army_supply.items():
            fancy_enemy_army += f'\n ~ | {key} x {value}\n'

        enemy_army_str = f"===Enemy Army==={fancy_enemy_army}"
        enemy_msg = f"===Enemy===\
                \n ~ | {enemy_worker_str} |\
                \n ~ | {enemy_army_str}\n "
        self.client.debug_text_2d(enemy_msg, Point2((0.65, 0.18)), None, 15)

    def update_army_attacker_tags(self):
        for key, value in self.army.items():
            for unit in value:
                if unit.is_attacking:
                    target = unit.order_target
                    if target and isinstance(target, int):
                        last_attacker_tag = target
                        #key: my army unit tag value: last enemy unit attacked
                        self.last_attacker_tags[unit.tag] = last_attacker_tag

    #internal update helpers
    def update_army_power(self):
        #get worker count and army count
        self.worker_count = len(self.cache.own(self.worker_type))
        self.army = {unit_type.name: self.cache.own(unit_type) for unit_type in self.unit_types}
        #update army supply
        self._update_army_supply()
        extended_power = self._calc_my_total_power()
        if extended_power:
            self.my_total_power._update_from(extended_power)

    def _update_army_supply(self):
        self.army_total = 0
        #calc from army supply
        for key, value in self.army.items():
            army_key_count = 0
            if value: army_key_count = max(len(value), 0)
            self.army_supply[key] = army_key_count
            self.army_total += army_key_count

        self.army_supply['TOTAL'] = self.army_total

    def update_enemy_army_power(self):
        #get worker count and army count
        self.enemy_worker_count =  max(self.enemy_units_manager.enemy_worker_count, 0)
        self.enemy_army = self.enemy_units_manager.enemy_composition
        #update enemy army supply
        self._update_enemy_army_supply()
        enemy_extended_power = self._calc_enemy_total_power()
        if enemy_extended_power:
            self.enemy_total_power._update_from(enemy_extended_power)
    def _update_enemy_army_supply(self):
        self.enemy_army_total = 0
        #calc from enemy army supply
        for unit_type in self.enemy_units_manager._known_enemy_units_dict:
            unit_type_count = max(self.enemy_units_manager.unit_count(unit_type), 0)
            self.enemy_army_supply[unit_type.name] = unit_type_count
            self.enemy_army_total += unit_type_count
        self.enemy_army_supply['TOTAL'] = self.enemy_army_total
    def _update_enemy_unit_states(self):
        types_check = set()
        inverted_last_attacker_tags = {v: k for k, v in self.last_attacker_tags.items()}
        for unit in self.ai.all_enemy_units:  # type: Unit
            real_type = self.unit_values.real_type(unit.type_id)

            if real_type not in types_check:
                types_check.add(real_type)

            # Ignore some units that are eg. temporary
            if real_type in ignored_types:
                continue

            if unit.is_snapshot:
                # Ignore snapshots aa they have a different tag than the "real" unit.
                continue

            if unit.is_hallucination:
                continue

            if not unit.is_visible:
                continue

            if 'egg' in str(unit.type_id).lower():
                continue
            if 'cocoon' in str(unit.type_id).lower():
                continue
            if 'tumor' in str(unit.type_id).lower():
                continue
                
            UnitState.update_unit_state(unit, self.ai.state.game_loop)

            if unit.tag in inverted_last_attacker_tags:
                # Now you have the attacker's tag
                attacker_tag = inverted_last_attacker_tags[unit.tag]
                UnitState.update_last_attacker(unit, attacker_tag)


    def _calc_my_total_power(self) -> PowerValues:
        """
        Returns the total power of all my units we currently know about.
        Assumes they are all in full health. Ignores workers and overlords.
        """
        total_power = ExtendedPower(self.unit_values)
        for unit_type in self.unit_types:
            if self.unit_values.is_worker(unit_type) or unit_type in self.supply_unit_types:
                continue
            count_for_unit_type = self.army_supply[unit_type.name]
            total_power.add_unit(unit_type, count_for_unit_type)
        return total_power
    def _calc_enemy_total_power(self) -> PowerValues:
        """
         Returns the total power of all enemy units we currently know about.
         Assumes they are all in full health. Ignores workers and overlords.
        """
        total_power = ExtendedPower(self.unit_values)
        for unit_type in self.enemy_units_manager._known_enemy_units_dict:
            if self.unit_values.is_worker(unit_type) or unit_type in self.supply_unit_types:
                continue
            count_for_unit_type = self.enemy_army_supply[unit_type.name]
            total_power.add_unit(unit_type, count_for_unit_type)
        return total_power

    def compare(self, power_types):
        if isinstance(power_types, (list, tuple)):
            diff_relative_powers = []
            for power_type in power_types:
                enemy_relative_power_value = self.enemy_total_power._calc_relative_power(power_type)
                relative_power_value = self.enemy_total_power._calc_relative_power(power_type)
                diff_relative_power_value = enemy_relative_power_value - relative_power_value
                #print(f"{self}::compare: relative_power_value: {type(relative_power_value)} = {relative_power_value}")
                diff_relative_powers.append(diff_relative_power_value)
            #print(f"{self}::compare: diff_relative_powers: {type(diff_relative_powers)} = {diff_relative_powers}")
            return diff_relative_powers
        elif isinstance(power_types, PowerTypeId):
            enemy_relative_power_value = self.enemy_total_power._calc_relative_power(power_types)
            relative_power_value = self.enemy_total_power._calc_relative_power(power_types)
            diff_relative_power = enemy_relative_power_value - relative_power_value
            #print(f"{self}::compare: diff_relative_power: {type(diff_relative_power)} = {diff_relative_power}")
            return diff_relative_power
        return 0.0



ignored_types: Set[UnitTypeId] = {
    # Zerg
    UnitTypeId.EGG,
    UnitTypeId.LARVA,
    UnitTypeId.INFESTORTERRAN,
    UnitTypeId.INFESTEDTERRANSEGG,
    UnitTypeId.CHANGELING,
    UnitTypeId.CHANGELINGMARINE,
    UnitTypeId.CHANGELINGMARINESHIELD,
    UnitTypeId.CHANGELINGZEALOT,
    UnitTypeId.CHANGELINGZERGLING,
    UnitTypeId.CHANGELINGZERGLINGWINGS,
    UnitTypeId.BROODLING,
    UnitTypeId.PARASITICBOMBDUMMY,  # wtf is this?
    UnitTypeId.LOCUSTMP,
    UnitTypeId.LOCUSTMPFLYING,
    # Terran
    UnitTypeId.MULE,
    UnitTypeId.KD8CHARGE,
    # Protoss
    # Adept is tricky, since the phase shift is temporary but
    # it should still be counted as an adept. just not twice.
    UnitTypeId.ADEPTPHASESHIFT,
    UnitTypeId.DISRUPTORPHASED,
}


# # Example usage:
# total_power = TotalPower(10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
# power_values = PowerValues(total_power)

# # Accessing power values
# print(power_values.power)
# print(power_values.air_presence)

# def calc_total_power(unit_values, unit_types, units):
#     total_power = ExtendedPower(self.unit_values)
#         for unit_type in self.enemy_units_manager._known_enemy_units_dict:
#             if self.unit_values.is_worker(unit_type) or unit_type == UnitTypeId.OVERLORD:
#                 continue
#             count_for_unit_type = cache.unit_count()
#             total_power.add_unit(unit_type, count_for_unit_type)
#         return PowerValues(total_power)

class MotherManagerBase(SingletonManager):
    def __init__(self):
        self.num_expansions = 0
        self.worker_type = UnitTypeId.SCV

        self._drones = 0
        self.expansion_bases = []

        # self.army = {}
        # self.army_supply = {}
        # self.enemy_army = {}
        # self.enemy_army_supply = {}
        
        # self.unit_types = []
        # self.my_total_power = PowerValues()
        # self.enemy_total_power = PowerValues()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        #print(format_table(knowledge))
        self.unit_values = knowledge.unit_values
        self.zone_manager = knowledge.zone_manager
        self.enemy_units_manager = knowledge.get_manager(IEnemyUnitsManager)
        self.build_detector = knowledge.get_manager(BuildDetector)
        self.create_expansion_base(self.zone_manager.own_main_zone)

    @property
    def rush_detected(self):
        rush_timing = 60 * 3
        return self.build_detector.rush_detected and self.ai.time < rush_timing  
    async def update(self):
        super().update()
        self._larva = len(self.cache.own(UnitTypeId.LARVA))
        self._drones = len(self.cache.own(self.worker_type))

        for zone in self.zone_manager.enemy_expansion_zones:
            if zone and zone._is_enemys:
                create_new_expansion_base(zone, is_ours=False)

        self.expansion_bases = list(ExpansionBase.Registry.values())

       
        #self.print(f"\n ~ | Drones: {self._drones} | Army: {army_supply} | Larva: {self._larva} |")
        #update my economy
        self.mineral_amount = self.ai.minerals
        self.gas_amount = self.ai.vespene
        self.mineral_rate = self.ai.state.score.collection_rate_minerals 
        self.gas_rate = self.ai.state.score.collection_rate_vespene
        
        num_ours = 0
        num_thiers = 0
        for expo in ExpansionBase.Registry.values():
            expo.update_status()
            if expo.is_ours:
                num_ours += 1
            else:
                num_thiers += 1
        ExpansionBase.num_expansions = num_ours
        ExpansionBase.num_enemy_expansions = num_thiers
            
        pass

    async def post_update(self):
        super().post_update()

        # for expo in ExpansionBase.Registry.values():
        #     expo.update_status()
        

    def create_expansion_base(self, expand_here: Zone):
        return create_new_expansion_base(expand_here)

from scipy import spatial

from sc2.game_info import Ramp

#from ..queens_sc2 import Creep
from sc2pathlib import *

previous_positions = {}

def update_unit_positions(units, current_frame):
    """
    Update and track the positions of units to calculate their velocity.
    
    :param units: List of units to track.
    :param current_frame: Current game frame number.
    """
    global previous_positions
    for unit in units:
        if unit.tag not in previous_positions:
            previous_positions[unit.tag] = (unit.position, current_frame)
        else:
            previous_positions[unit.tag] = (unit.position, current_frame)

def calculate_velocity(unit, current_frame):
    """
    Calculate the velocity of a unit based on its change in position over time.
    
    :param unit: The unit to calculate the velocity for.
    :param current_frame: Current game frame number.
    :return: Estimated velocity as a numpy array.
    """
    if unit.tag not in previous_positions:
        return np.array([0.0, 0.0])
    
    previous_position, previous_frame = previous_positions[unit.tag]
    if current_frame == previous_frame:
        return np.array([0.0, 0.0])
    
    delta_time = current_frame - previous_frame
    current_position = np.array([unit.position.x, unit.position.y])
    previous_position = np.array([previous_position.x, previous_position.y])
    
    velocity = (current_position - previous_position) / delta_time
    return velocity


#pos: [Point2] = self._find_closest_to_target(creep_target, self.creep_map)
class TerrainManager(SingletonManager):
    def __init__(self):
        self.expansions: List[Point2] = []

        self.optimal_nydus_location: Point2 = (0,0)
        self.nydus_locations: List[Point2] = []

        self.nydus_solver:NydusSolver = None

        self.path_finder_terrain: PathFinder = None

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        #self.expansion_paths_updater = IntervalFunc(self.ai, self._path_expansion_distances, 1)
        self._calculate_nydus_spots()
        self._path_expansion_distances()
        game_info: GameInfo = self.ai.game_info
        self.nydus_solver = NydusSolver(game_info, self.ai)
        #self.optimal_nydus_location , self.nydus_locations = self.nydus_solver.calculate_nydus_spots(12)
        self.offensive_nydus_locations = []
        self.defensive_nydus_locations = []

        self.creep_map: np.ndarray
        self.no_creep_map: np.ndarray
        # self.creep_map  = Creep.get_creep_map()
        # self.no_creep_map  = Creep.get_no_creep_map()
        self.overlord_spots = self.knowledge.pathing_manager.overlord_spots
        self.init_custom_path_finder()

    def update_creep_map(self) -> None:
        creep: np.ndarray = np.where(self.ai.state.creep.data_numpy == 1)
        self.creep_map = np.vstack((creep[1], creep[0])).transpose()
        no_creep: np.ndarray = np.where(
            (self.ai.state.creep.data_numpy == 0)
            & (self.ai.game_info.pathing_grid.data_numpy == 1)
        )
        self.no_creep_map = np.vstack((no_creep[1], no_creep[0])).transpose()
    
    def init_custom_path_finder(self):
        #setup stuff to get path finder terrain
        game_info: GameInfo = self.ai.game_info
        path_grid = game_info.pathing_grid
        placement_grid = game_info.placement_grid
        _data = np.fmax(path_grid.data_numpy, placement_grid.data_numpy).T
        self.path_finder_terrain = PathFinder(_data)
        self.path_finder_terrain.normalize_influence(20)
        self.knowledge.pathing_manager.set_rocks(self.path_finder_terrain)
        enemy_influence_source_location = self.knowledge.zone_manager.enemy_expansion_zones[1].gather_point

        # lets add influence from enemy natural towards map center
        self.percentage_middle_avoid = 0.75
        default_path, _ = self.knowledge.pathing_manager.map.find_path(0, enemy_influence_source_location, game_info.map_center)        
        self.path_finder_terrain.add_influence(list(Point2(default_path[i]) for i in range(int(len(default_path) * self.percentage_middle_avoid),5)),value=100, distance=10)

        log_info(f" ~ path_finder_terrain: \n{self.path_finder_terrain}")

    async def update(self):
        super().update()
        
        #self.expansion_paths_updater.execute()

        self.update_creep_map()

        #self.offensive_nydus_locations = self.nydus_solver.calculate_offensive_nydus_spots(ExpansionBase.num_enemy_expansions)
        #self.defensive_nydus_locations = self.nydus_solver.calculate_defensive_nydus_spots(ExpansionBase.num_expansions)
        
        


        #self.add_enemy_avoidance_influence()
    def add_no_creep_avoidance_influence(self):
        # Construct Point2 objects from the no_creep_map
        no_creep_points = [Point2(pos) for pos in self.no_creep_map]
        #add extra influence for no_creep map
        self.path_finder_terrain.add_influence(no_creep_points,value=100, distance=10)
    def add_creep_avoidance_influence(self):
        # Construct Point2 objects from the no_creep_map
        creep_points = [Point2(pos) for pos in self.creep_map]
        #add extra influence for no_creep map
        self.path_finder_terrain.add_influence(creep_points,value=-100, distance=10)
    def add_enemy_avoidance_influence(self, target):
        enemy_influence_source_location = self.knowledge.zone_manager.enemy_expansion_zones[1].gather_point
        #percentage_middle_avoid = 0.75
        # lets add influence from enemy natural towards map center
        
        # lets add influence from enemy natural towards where we want to end up, so we tend to favour other side to approach
        default_path, _ = self.knowledge.pathing_manager.map.find_path(0, enemy_influence_source_location, target)        
        self.path_finder_terrain.add_influence(list(Point2(default_path[i]) for i in range(int(len(default_path) * self.percentage_middle_avoid),5)),value=100, distance=10)


    @property
    def enemy_main_base_ramp(self) -> Ramp:
        """Works out which ramp is the enemies main

        Returns:
            Ramp -- SC2 Ramp object
        """
        return min(
            (
                ramp
                for ramp in self.ai.game_info.map_ramps
                if len(ramp.upper) in {2, 5}
            ),
            key=lambda r: self.ai.enemy_start_locations[0].distance_to(r.top_center),
        )

    @property
    def natural_location(self) -> Point2:
        if len(self.expansions) > 0:
            return self.expansions[0][0]

    @property
    def defensive_third(self) -> Point2:
        """
        Get the third furthest from enemy
        @return:
        """
        third_loc: Point2 = self.expansions[1][0]
        fourth_loc: Point2 = self.expansions[2][0]

        third_distance_to_enemy: float = third_loc.distance_to(
            self.ai.enemy_start_locations[0]
        )
        fourth_distance_to_enemy: float = fourth_loc.distance_to(
            self.ai.enemy_start_locations[0]
        )

        return (
            third_loc
            if third_distance_to_enemy >= fourth_distance_to_enemy
            else fourth_loc
        )

    async def post_update(self):
        super().post_update()
        # draw_text_on_world(self.ai, self.optimal_nydus_location, f"BEST-NYDUS #0 HERE: {self.optimal_nydus_location}")
        # for i, nydus_spot in enumerate(self.nydus_locations):
        #     draw_text_on_world(self.ai, nydus_spot, f"BEST-NYDUS #{i+1} HERE: {nydus_spot}")

        # for i, nydus_spot in enumerate(self.offensive_nydus_locations):
        #     draw_text_on_world(self.ai, nydus_spot, f"ATK-NYDUS #{i+1} HERE: {nydus_spot}")
        # for i, nydus_spot in enumerate(self.defensive_nydus_locations):
        #     draw_text_on_world(self.ai, nydus_spot, f"DEF-NYDUS #{i+1} HERE: {nydus_spot}")


        for i, overlord_spot in enumerate(self.overlord_spots):
            draw_text_on_world(self.ai, overlord_spot, f"OVERLORD #{i+1} HERE: {overlord_spot}")

    def get_behind_mineral_positions(self, th_pos: Point2) -> List[Point2]:
        """Thanks to sharpy"""
        positions: List[Point2] = []
        possible_behind_mineral_positions: List[Point2] = []

        all_mf: Units = self.ai.mineral_field.closer_than(10, th_pos)

        if all_mf:
            for mf in all_mf:
                possible_behind_mineral_positions.append(th_pos.towards(mf.position, 9))

            positions.append(th_pos.towards(all_mf.center, 9))  # Center
            positions.insert(
                0, positions[0].furthest(possible_behind_mineral_positions)
            )
            positions.append(positions[0].furthest(possible_behind_mineral_positions))
        else:
            positions.append(th_pos.towards(self.ai.game_info.map_center, 5))
            positions.append(th_pos.towards(self.ai.game_info.map_center, 5))
            positions.append(th_pos.towards(self.ai.game_info.map_center, 5))

        return positions

    def _calculate_nydus_spots(self) -> None:
        game_info = self.ai.game_info
        # create KDTree for nearest neighbor searching
        standin = [
            (x, y)
            for x in range(game_info.pathing_grid.width)
            for y in range(game_info.pathing_grid.height)
        ]
        tree = spatial.KDTree(standin)

        # get the height of the enemy main to make sure we find the right tiles
        enemy_height: float = game_info.terrain_height[
            self.ai.enemy_start_locations[0].rounded
        ]

        # find the gases and remove points with in 9 of them
        enemy_gases = self.ai.vespene_geyser.closer_than(
            12, self.ai.enemy_start_locations[0].rounded
        )
        gas_one = [
            standin[x] for x in tree.query_ball_point(enemy_gases[0].position, 11.5)
        ]
        gas_two = [
            standin[y] for y in tree.query_ball_point(enemy_gases[1].position, 11.5)
        ]
        close_to_gas = set(gas_one + gas_two)

        # find the enemy main base pathable locations
        enemy_main = [
            standin[z]
            for z in tree.query_ball_point(
                self.ai.enemy_start_locations[0].position, 45
            )
            if game_info.terrain_height[standin[z]] == enemy_height
            and game_info.pathing_grid[standin[z]] == 1
        ]

        # find the enemy ramp so we can avoid it
        close_to_ramp = [
            standin[z]
            for z in tree.query_ball_point(self.enemy_main_base_ramp.top_center, 18)
        ]

        # main base, but without points close to the ramp or gases
        main_away_from_gas_and_ramp = list(
            set(enemy_main) - close_to_gas - set(close_to_ramp)
        )

        # get a matrix of the distances from the points to the enemy main
        distances = spatial.distance_matrix(
            main_away_from_gas_and_ramp,
            [self.ai.enemy_start_locations[0].position.rounded],
        )

        # select the point with the greatest distance from the enemy main
        self.optimal_nydus_location = Point2(
            main_away_from_gas_and_ramp[np.where(distances == max(distances))[0][0]]
        )

        # get other positions in the enemy main for potential follow-up nyduses
        possible_nydus_locations = np.array(main_away_from_gas_and_ramp)[
            np.where(distances[:, 0] > 13)[0]
        ]
        edge = [
            Point2(loc)
            for loc in possible_nydus_locations
            if not all([game_info.pathing_grid[x] for x in Point2(loc).neighbors8])
        ]

        self.nydus_locations = edge

    async def _path_expansion_distances(self):
        """Calculates pathing distances to all expansions on the map"""
        expansion_distances = []
        for el in self.ai.expansion_locations_list:
            if (
                self.ai.start_location.distance_to(el)
                < self.ai.EXPANSION_GAP_THRESHOLD
            ):
                continue

            distance = await self.ai.client.query_pathing(self.ai.start_location, el)
            if distance:
                expansion_distances.append((el, distance))
        # sort by path length to each expansion
        expansion_distances = sorted(expansion_distances, key=lambda x: x[1])
        return expansion_distances

class MikaGroupCombatManager(GroupCombatManager):
    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)

    def action_to(self, group: CombatUnits, target, move_type: MoveType, is_attack: bool):
        #replace with current terrain manager pather
        
        #TerrainManager.get_instance().add_enemy_avoidance_influence(target)
        TerrainManager.get_instance().add_no_creep_avoidance_influence()
        TerrainManager.get_instance().add_creep_avoidance_influence()

        self.pather.path_finder_terrain = TerrainManager.get_instance().path_finder_terrain

        original_target = target
        if isinstance(target, Point2) and group.ground_units:
            if move_type in {MoveType.DefensiveRetreat, MoveType.PanicRetreat}:
                target = self.pather.find_influence_ground_path(group.center, target, 14)
            else:
                target = self.pather.find_path(group.center, target, 14)

        own_unit_cache: Dict[UnitTypeId, Units] = {}

        for unit in group.units:
            real_type = self.unit_values.real_type(unit.type_id)
            units = own_unit_cache.get(real_type, Units([], self.ai))
            if units.amount == 0:
                own_unit_cache[real_type] = units

            units.append(unit)

        for type_id, type_units in own_unit_cache.items():
            micro: MicroStep = self.unit_micros.get(type_id, self.generic_micro)
            micro.init_group(self.rules, group, type_units, self.enemy_groups, move_type, original_target)
            group_action = micro.group_solve_combat(type_units, Action(target, is_attack))

            for unit in type_units:
                final_action = micro.unit_solve_combat(unit, group_action)
                final_action.to_commmand(unit)

                if self.debug:
                    if final_action.debug_comment:
                        status = final_action.debug_comment
                    elif final_action.ability:
                        status = final_action.ability.name
                    elif final_action.is_attack:
                        status = "Attack"
                    else:
                        status = "Move"
                    if final_action.target is not None:
                        if isinstance(final_action.target, Unit):
                            status += f": {final_action.target.type_id.name}"
                        else:
                            status += f": {final_action.target}"

                    status += f" G: {group.debug_index}"
                    status += f"\n{move_type.name}"

                    pos3d: Point3 = unit.position3d
                    pos3d = Point3((pos3d.x, pos3d.y, pos3d.z + 2))
                    self.ai._client.debug_text_world(status, pos3d, size=10)
