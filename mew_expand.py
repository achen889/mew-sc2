import sys
import time

from typing import List, Optional, Union

from sc2.position import Point2, Point3, Pointlike
from sc2.ids.unit_typeid import UnitTypeId

from sharpy.constants import Constants
from sharpy.managers.core import *
from sharpy.managers.core.roles import UnitTask
from sharpy.general.zone import Zone
from sharpy.tools import IntervalFunc 
from sharpy.sc2math import points_on_circumference_sorted
from sharpy.utils import map_to_point2s_minerals
from sharpy.general.extended_power import ExtendedPower
from sharpy.plans.zerg import *
from sharpy.plans.protoss import *

class ExpansionBase():
    cur_id = 0
    num_expansions = 0 #own expansions
    num_enemy_expansions = 0
    Registry = {}
    def __init__(self, zone: Zone, is_ours=True):
        self.id = ExpansionBase.cur_id = ExpansionBase.cur_id + 1
        self.zone = zone
        self.desired_workers = 0
        
        self.mineral_fields = []
        self.vespene_geysers = []
        #self.queens = []
        
        #for enemies
        self.is_ours = is_ours
        #tracking
        self._townhall = None
        self._workers = []
        self._units = []
        self._power = None
        self._attacking_units = []
        self._attacking_power = None
        # self.zone.update()
        #self.update_status()
    @property
    def center_location(self):
        return self.zone.center_location
    @property
    def gather_point(self):
        return self.zone.gather_point

    def update_status(self):
        #self.zone.update()
        #print(format_table(self.zone))
        self.mineral_fields = self.zone.mineral_fields
        self.vespene_geysers = self.zone.gas_buildings
        self.desired_workers = 3 * len(self.get_resource_nodes())
        self.is_ours = self.zone.is_ours
        
        if self.zone.cache:
            self._townhall = self.zone.our_townhall if self.is_ours else self.zone.enemy_townhall
            self._workers = self.zone.our_workers if self.is_ours else self.zone.enemy_workers
            self._units = self.zone.our_units if self.is_ours else self.zone.known_enemy_units
            self._power = self.zone.our_power if self.is_ours else self.zone.known_enemy_power

            if self.is_ours:
                self._attacking_units = self.zone.assaulting_enemies
                self._attacking_units = self.zone.assaulting_enemy_power

    def get_resource_nodes(self):
        out_nodes = []
        if self.mineral_fields:
            out_nodes += self.mineral_fields
        if self.vespene_geysers:
            out_nodes += self.vespene_geysers
        return out_nodes

         
    def print(self):
        print(f'ExpansionBase: id: {self.id} workers: {self.desired_workers} / {self.workers} hatcheries: {self.hatcheries } queens: {self.queens}')

class SmartExpand(Expand):
    
    def __init__(
        self,
        to_count: int,
        priority: bool = False,
        consider_worker_production: bool = True,
        priority_base_index: Optional[int] = None, 
        ):
        super().__init__(to_count, priority, consider_worker_production, priority_base_index)
        #print(format_table(self))

    async def build_expansion(self, expand_here: "Zone") -> bool:
        result = await super().build_expansion(expand_here)
        if result:
           new_expo = create_new_expansion_base(expand_here)
           return result
   

    async def execute(self) -> bool:
        result = await super().execute()
        if result:
            #print(format_table(self))
            return result

def create_new_expansion_base(expo_zone: Zone, is_ours = True):
    new_expo = ExpansionBase(expo_zone, is_ours)
    #ExpansionBase.num_expansions+=1

    if expo_zone.center_location not in ExpansionBase.Registry:
        #print(format_table(new_expo))
        ExpansionBase.Registry[expo_zone.center_location] = new_expo
    return new_expo

class BalancedDistributeWorkers(DistributeWorkers):

    async def execute(self) -> bool:
        #self.adjust_balance()
        return await super().execute()

    def adjust_balance(self):
        self._drones = len(self.cache.own(UnitTypeId.DRONE))
        mineral_amount = self.ai.minerals
        gas_amount = self.ai.vespene
        mineral_rate = self.ai.state.score.collection_rate_minerals 
        gas_rate = self.ai.state.score.collection_rate_vespene

        # mineral_str = ansi_color_str(f"Minerals: {mineral_amount} +{mineral_rate}/s", fg='white',bg='cyan')
        # gas_str = ansi_color_str(f"Vespene: {gas_amount} +{gas_rate}/s", fg='white',bg='green')
        # self.print(f"\n ~ | {mineral_str} |\n ~ | {gas_str} |")

def find_any_enemy_expos(combat_units, zone_manager):
    vulnerable_enemy_expos = []
    #skip main and maybe natural, assume too heavily guarded
    enemy_expo_zones = zone_manager.enemy_expansion_zones[1:]
    for enemy_expo_zone in enemy_expo_zones:
        if enemy_expo_zone._is_enemys:
            enemy_power = enemy_expo_zone.known_enemy_power
            our_power = combat_units.power
            if enemy_expo_zone.center_location in ExpansionBase.Registry:
                enemy_expo_base = ExpansionBase.Registry[enemy_expo_zone.center_location]
                if enemy_expo_base and not enemy_expo_base.is_ours:
                        #check for enemy town hall and workers
                        if enemy_expo_base._townhall and len(enemy_expo_zone.enemy_workers) > 0:
                            
                            vulnerability_score = (our_power.ground_power / (enemy_power.ground_power + 1)) * 0.5 + (our_power.air_power / (enemy_power.air_power + 1)) * 0.5
                            vulnerable_enemy_expos.append((enemy_expo_zone, vulnerability_score))
    vulnerable_enemy_expos.sort(key=lambda x: x[1], reverse=True)
    return [zone for zone, score in vulnerable_enemy_expos]