from typing import List, Optional, Union
import sys
import time

from sharpy.sc2math import points_on_circumference_sorted
from sc2.position import Point2
from sharpy.managers.core.roles import UnitTask
from sharpy.tools import IntervalFunc

from sc2.data import Race
from sharpy.plans.acts.morph_building import MorphBuilding
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sharpy.general.extended_power import ExtendedPower
from sc2.units import Units
from sharpy.constants import Constants
from sharpy.combat.group_combat_manager import GroupCombatManager
from sharpy.plans.zerg import *
from sharpy.sc2math import points_on_circumference_sorted
from sharpy.utils import map_to_point2s_minerals
from sharpy.plans.tactics import SpeedMining, PlanWorkerOnlyDefense
from sharpy.general.zone import Zone


from .mew_manager import MotherManagerBase

class CounterTerranTie2(BuildOrder):
    def __init__(self, orders: List[Union[ActBase, List[ActBase]]]):
        """
        Build order package that replaces normal build order for Zerg with one that builds mutalisks to destroy terran
        flying buildings.
        Add any DistributeWorkers acts with orders
        """
        cover_list = SequentialList(
            [
                WorkerScout(),
                ScoutZone(),
                DistributeWorkers(),
                AutoOverLord(),
                Step(None, ZergUnit(UnitTypeId.DRONE, 20), skip=Supply(198)),
                StepBuildGas(4, None),
                MorphLair(),
                ActBuilding(UnitTypeId.SPIRE, 1),
                Step(
                    None,
                    DefensiveBuilding(UnitTypeId.SPORECRAWLER, DefensePosition.BehindMineralLineCenter),
                    skip_until=Supply(199),
                ),
                Step(
                    None, DefensiveBuilding(UnitTypeId.SPINECRAWLER, DefensePosition.Entrance), skip_until=Supply(199),
                ),
                ZergUnit(UnitTypeId.MUTALISK, 21),
            ]
        )

        new_build_order = [
            Step(None, cover_list, skip_until=self.should_build_mutalisks),
            Step(None, BuildOrder(orders), skip=self.should_build_mutalisks),
        ]
        super().__init__(new_build_order)

    def should_build_mutalisks(self, knowledge):
        if self.knowledge.enemy_race != Race.Terran:
            return False

        # if len(self.cache.own({UnitTypeId.MUTALISK, UnitTypeId.CORRUPTOR})) >= 10:
        #     return False

        if len(self.ai.enemy_units.not_flying) > 1:
            return False

        if self.ai.supply_workers < 20 and self.ai.supply_used < 190:
            return False

        if self.ai.supply_used < 70:
            return False

        main_zone: Zone = self.zone_manager.enemy_main_zone
        if not main_zone.is_scouted_at_least_once:
            return False

        buildings = self.ai.enemy_structures
        return len(buildings) == len(buildings.flying)


class ScoutZone(ActBase):
    def __init__(self, unit_type=UnitTypeId.ZERGLING, scout_zone=None, action=None):
        self.position_updater: IntervalFunc = None
        self.scout: Unit = None
        self.scout_tag = None
        self.unit_type = unit_type
        self.scout_zone = scout_zone
        self.action = action
        self.enemy_ramp_top_scouted: bool = None

        self.last_scout_time = sys.maxsize

        # This is used for stuck / unreachable detection
        self.last_locations: List[Point2] = []

        # An ordered list of locations to scout. Current target
        # is first on the list, with descending priority, ie.
        # least important location is last.
        self.scout_locations: List[Point2] = []
    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.zone_manager = knowledge.zone_manager
        self.position_updater = IntervalFunc(knowledge.ai, self.update_position, 1)
        #self.ai = knowledge.ai
    async def select_scout(self):
        if self.scout_tag is not None:
            self.scout = self.roles.get_unit_by_tag_from_task(self.scout_tag, UnitTask.Scouting)
            return

        free_units_of_type = self.roles.free_units.of_type(self.unit_type)
        if free_units_of_type:
            if len(free_units_of_type) > 0 and free_units_of_type.exists:
                if self.scout_tag is None: 
                    closest_unit_of_type = free_units_of_type[0]  
                    if self.current_target:
                        closest_unit_of_type = free_units_of_type.closest_to(self.current_target)
                    # else:
                    #     closest_unit_of_type = free_units_of_type[0]
                    
                    if closest_unit_of_type:
                        self.scout_tag = closest_unit_of_type.tag
                        self.roles.set_task(UnitTask.Scouting, closest_unit_of_type)
                        self.scout = closest_unit_of_type
                        self.print(f"select new scout: {self.scout} -> current target: {self.current_target}")
                        return
    def update_position(self):
        if self.scout:
            self.last_locations.append(self.scout.position)

    async def scout_locations_upkeep(self):
        if len(self.scout_locations) > 0:
            return

        self.scout_locations.clear()

        enemy_base_found = self.zone_manager.enemy_start_location_found

        enemy_base_scouted = (
            enemy_base_found
            and self.zone_manager.enemy_main_zone.is_scouted_at_least_once
            and self.zone_manager.enemy_main_zone.scout_last_circled
        )

        enemy_base_blocked = (
            enemy_base_found
            and self.enemy_ramp_top_scouted
            and await self.target_unreachable(self.zone_manager.enemy_main_zone.behind_mineral_position_center)
        )

        if not self.scout_zone:
            if enemy_base_scouted or enemy_base_blocked:
                # When enemy found and enemy main base scouted, scout nearby expansions
                self.scout_enemy_expansions()
            elif (
                enemy_base_found
                and self.enemy_ramp_top_scouted
                and self.scout.distance_to(self.zone_manager.enemy_main_zone.center_location) < 40
            ):

                self.circle_location(self.zone_manager.enemy_main_zone.center_location)
                self.zone_manager.enemy_main_zone.scout_last_circled = self.knowledge.ai.time
            else:
                self.scout_start_locations()
        else:
            #go to ramp
            if self.scout_zone.ramp:
                self.scout_locations.append(self.scout_zone.ramp.top_center)
            #circle first
            location = self.scout_zone.center_location
            #self.scout_locations += points_on_circumference_sorted(location, self.ai.start_location, 10, 30)
            #self.scout_locations += map_to_point2s_minerals(self.scout_zone)

            #self.scout_locations.append(self.scout_zone.center_location + self.scout_zone.behind_mineral_position_center * 0.5)

            #go to center
            self.scout_locations.append(self.scout_zone.center_location)
            

    def scout_start_locations(self):
        self.print("Scouting start locations")
        self.enemy_ramp_top_scouted = False

        if self.scout:
            distance_to = self.scout.position
        else:
            distance_to = self.ai.start_location

        closest_distance = sys.maxsize
        for zone in self.zone_manager.unscouted_enemy_start_zones:
            distance = zone.center_location.distance_to(distance_to)
            # Go closest unscouted zone
            if distance < closest_distance:
                self.scout_locations.clear()

                if zone.ramp:
                    # Go ramp first
                    enemy_ramp_top_center = zone.ramp.top_center
                    self.scout_locations.append(enemy_ramp_top_center)

                # Go center of zone next
                self.scout_locations.append(zone.center_location)
                closest_distance = distance

        self.print(f"Scouting enemy base at locations {self.scout_locations}")

    def circle_location(self, location: Point2):
        self.scout_locations.clear()

        self.scout_locations = points_on_circumference_sorted(location, self.scout.position, 10, 30)
        self.print(f"Circling location {location}")

    def scout_enemy_expansions(self):
        if not self.zone_manager.enemy_start_location_found:
            return

        self.scout_locations.clear()

        self.scout_locations = map_to_point2s_minerals(self.zone_manager.enemy_expansion_zones[0:5])
        self.print(f"Scouting {len(self.scout_locations)} expansions from enemy base towards us")

    def distance_to_scout(self, location):
        # Return sys.maxsize so that the sort function does not crash like it does with None
        if not self.scout:
            return sys.maxsize

        if not location:
            return sys.maxsize

        return self.scout.distance_to(location)
    async def target_unreachable(self, target) -> bool:
        if target is None:
            return False

        start = self.scout
        if (
            len(self.last_locations) < 5
            or self.scout.distance_to(self.last_locations[-1]) > 1
            or self.scout.distance_to(self.last_locations[-2]) > 1
        ):
            # Worker is still moving, it's not stuck
            return False

        end = target

        result = await self.ai._client.query_pathing(start, end)
        return result is None
    def target_location_reached(self):
        #last_location = self.scout_locations[:-1]
        if len(self.scout_locations) > 0:
            self.scout_locations.pop(0)

        self.execute_custom_action()
        # if self.scout_zone:
        #     self.circle_location(self.scout_zone.center_location)
            #self.scout_enemy_expansions()
            
            
    @property
    def current_target(self) -> Optional[Point2]:
        if len(self.scout_locations) > 0:
            return self.scout_locations[0]
        return None

    @property
    def current_target_is_enemy_ramp(self) -> bool:
        for zone in self.zone_manager.expansion_zones:  # type: Zone
            if zone.ramp and self.current_target == zone.ramp.top_center:
                return True
        return False
    def execute_custom_action(self):
        if self.action:
            # Execute the specified action or ability
            self.scout(self.action, self.scout.position)
    async def execute(self) -> bool:    
        await self.scout_locations_upkeep()
        await self.select_scout()
        if self.scout is None:
            # No one to scout
            return True  # Non blocking

        self.roles.refresh_task(self.scout)

        #if < 30 sec since last time scouted
        scout_interval = 60
        cur_time = self.ai.time
        elapsed_time_since_last_scouted = abs(cur_time - self.last_scout_time)
        if elapsed_time_since_last_scouted < scout_interval:
            return True

        if not len(self.scout_locations):

            # Nothing to scout
            return True  # Non blocking

        self.position_updater.execute()
        dist = self.distance_to_scout(self.current_target)
        
        if dist < Constants.SCOUT_DISTANCE_THRESHOLD:
            self.print(f"{self.scout} reached target at {self.current_target}")
            # if self.unit_type == UnitTypeId.ZERGLING:
            #     #target_location = self.current_target 
            #     self.scout(AbilityId.BURROWDOWN_ZERGLING, self.scout.position)
            self.target_location_reached()
            self.last_scout_time = self.ai.time
        if await self.target_unreachable(self.current_target):
            self.print(f"{self.scout} target at {self.current_target} unreachable!")
            self.target_location_reached()
            self.last_scout_time = self.ai.time
        if self.scout is not None and self.current_target is not None:
            #self.print(f"{self.scout} move to target: {self.current_target}")
            self.scout.move(self.current_target)


        return True  # Non blocking

#AbilityId.BURROWDOWN_ZERGLING

class ScoutParty(BuildOrder):
    def __init__(self, unit_type=UnitTypeId.ZERGLING, unit_count=6, action=None):
        self.enemy_expansion_zones = []
        self.unit_type = unit_type
        self.scout_party = []
        self.action = action
        self.scouts_dispatched = False  # Flag to track if scouts have been dispatched
        self.last_dispatch_time = None  # Track the time of the last dispatch
        self.refresh_delay = 60 * 2
        
        self.scout_party.append(ScoutZone())
        for i in range(1, unit_count-1):
            self.scout_party.append(ScoutZone()) #action=AbilityId.BURROWDOWN_ZERGLING)
        super().__init__(*self.scout_party)
    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.zone_manager = knowledge.zone_manager
    async def update_scout_party(self):
        self.enemy_expansion_zones = self.zone_manager.enemy_expansion_zones
        self.scout_party[0].scout_zone = self.enemy_expansion_zones[0]
        if self.debug : update_scout_party_str = f"\n ~ | {self.unit_type.name}#0 scouting zone!\n ~ | zone( index: {self.scout_party[0].scout_zone.zone_index} pos: {self.scout_party[0].scout_zone.center_location})"
        for i, enemy_expo_zone in enumerate(self.enemy_expansion_zones):
            if i > 0 and i < len(self.scout_party):
                scout_unit = self.scout_party[i]
                scout_unit.scout_zone = enemy_expo_zone
                if self.debug : update_scout_party_str += f"\n ~ | {self.unit_type.name}_#{i} scouting zone!\n ~ | zone( index: {scout_unit.scout_zone.zone_index} pos: {scout_unit.scout_zone.center_location} )"
        if self.debug : self.print(update_scout_party_str)
        pass

    async def execute(self) -> bool:
        
        #scout enemy main

        await self.update_scout_party()

        #scout enemy expo locations
        # if not self.scouts_dispatched:
            
        #     self.scouts_dispatched = True  # Mark scouts as dispatched
        #     self.last_dispatch_time = self.ai.time  # Update last dispatch time
        #     return self.update_scout_party()  # Dispatch scouts if not already dispatched or if refresh delay elapsed
        # else:
        #     if (self.last_dispatch_time and self.ai.time - self.last_dispatch_time > self.refresh_delay):
        #         self.scouts_dispatched = False  
        #         self.last_dispatch_time = None

        return await super().execute()



class IntervalTime(RequireBase):
    def __init__(self, time_interval: float = 60, duration: float = 6):
        assert time_interval is not None and isinstance(time_interval, (int, float))
        assert duration is not None and isinstance(duration, (int, float))
        super().__init__()
        self.last_trigger_time = -time_interval  # Initialize with a negative value to trigger immediately
        self.time_interval = time_interval
        self.duration = duration
        self.active_start_time = None

    def check(self) -> bool:
        current_time = self.ai.time
        if current_time - self.last_trigger_time >= self.time_interval:
            self.last_trigger_time = current_time
            self.active_start_time = current_time
            return True
        elif self.active_start_time is not None and current_time - self.active_start_time <= self.duration:
            return True
        else:
            return False



def handle_extractor_trick(bot):
        def extractor_trick(bot, num_gas=1) -> SequentialList:
            print(f'{bot}::extractor_trick: {num_gas}')
            return SequentialList(
                Step(Supply(14),BuildGas(num_gas),
                    skip=UnitExists(
                        UnitTypeId.EXTRACTOR, 
                        num_gas,
                        include_killed=True, include_pending=True
                    )
                ),
                Step(
                    UnitExists(
                        UnitTypeId.EXTRACTOR,
                        num_gas,
                        include_pending=True,
                        include_not_ready=True,
                    ),
                    ZergUnit(UnitTypeId.DRONE, to_count=14),
                ),
                # SequentialList will take care of making sure the drone was made
                Step(
                    UnitExists(UnitTypeId.EXTRACTOR, 2),
                    CancelBuilding(UnitTypeId.EXTRACTOR, to_count=0),
                    skip=UnitExists(
                        UnitTypeId.EXTRACTOR,
                        num_gas,
                        include_killed=True,
                        include_not_ready=False,
                    ),
                ),
            )
        return SequentialList(
            Step(None, ZergUnit(UnitTypeId.DRONE, to_count=14, only_once=True)),
            Step(Supply(14),
                extractor_trick(bot, 2),
                skip=UnitExists(
                    UnitTypeId.EXTRACTOR,
                    1,
                    include_killed=True,
                    include_not_ready=False,
                ),
            )
        )

from enum import Enum
 
class MewDefensePosition(Enum):
    CenterMineralLine = 0
    BehindMineralLineCenter = 1
    BehindMineralLineLeft = 2
    BehindMineralLineRight = 3
    Entrance = 4
    FarEntrance = 5

def get_defense_position(zone: Zone, position_type: MewDefensePosition) -> Point2:
    if position_type == MewDefensePosition.CenterMineralLine:
        return zone.center_location.towards(zone.behind_mineral_position_center, 4)
    if position_type == MewDefensePosition.BehindMineralLineCenter:
        return zone.behind_mineral_position_center
    if position_type == MewDefensePosition.BehindMineralLineLeft:
        return zone.behind_mineral_positions[0]
    if position_type == MewDefensePosition.BehindMineralLineRight:
        return zone.behind_mineral_positions[2]
    if position_type == MewDefensePosition.Entrance:
        return zone.center_location.towards(zone.gather_point, 5)
    if position_type == MewDefensePosition.FarEntrance:
        return zone.center_location.towards(zone.gather_point, 9)
    return zone.center_location
