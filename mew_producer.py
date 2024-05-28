from sharpy.plans.acts import ActBase, Tech, MorphWarpGates, GridBuilding
from sharpy.plans.acts.morph_building import MorphBuilding
from sharpy.plans import BuildOrder, SequentialList, Step

from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

from sc2.dicts.unit_train_build_abilities import TRAIN_INFO
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.dicts.unit_abilities import UNIT_ABILITIES

from typing import Dict, Set

from sc2.position import Point2, Point3, Pointlike
from sc2.unit import Unit
from sc2.units import Units

from sharpy.plans.require.supply import SupplyType

from .mew_common import _get_unit_trained_from, _get_train_ability_id, _get_abilities, log_evaluate_unit_data


import time

class ProductionStatusEntry():
    def __init__(self, unit_type, progress):
        self.unit_type = unit_type
        self.progress = progress
    @property
    def progress_percent(self):
        return self.progress * 100.0

    def __str__(self):
        return f'''\n ~ | unit type: {self.unit_type.name if self.unit_type else "None" } progress: {self.progress_percent:.2f}% |{"=" * int(20 * self.progress)}|'''

class ManageProductionBase(ActBase):
    def __init__(self, producer_unit_type):
        self.producer_unit_type = producer_unit_type
        self.production_status = {}
        self.production_line = {}

        # self.abilities = get_abilities(self.producer_unit_type)
        # print("=" * 80)



    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.knowledge = knowledge
        self.cache = self.knowledge.unit_cache
        self.all_producers_of_type : Units = self.cache.own(self.producer_unit_type)
        self.last_report_time = time.time()
        self._debug = True

    async def execute(self) -> bool:
        await self.organize_producers()
        await self.manage_producers()
        return True

    async def organize_producers(self):
        if self.cache.own(self.producer_unit_type) and len(self.cache.own(self.producer_unit_type)) > 0:
            self.all_producers_of_type = [unit for unit in self.cache.own(self.producer_unit_type) if unit.is_ready]
            #training_progress = 0
            production_reports = []
            
            for producer in self.all_producers_of_type:
                training_progress = producer.build_progress
                if producer.tag not in self.production_status:
                    self.production_status[producer.tag] = ProductionStatusEntry(self.producer_unit_type,training_progress)
                if producer.is_ready:
                    if producer.is_idle:
                        self.production_status[producer.tag].unit_type = None
                    
                    training_progress = 0
                    #update training progress   
                    if producer.orders and len(producer.orders) == 1:
                        training_progress = max(training_progress, producer.orders[0].progress)
                    elif producer.has_reactor and len(producer.orders) == 2:
                        training_progress = max(training_progress, producer.orders[1].progress)
                 
                self.production_status[producer.tag].progress = training_progress
                if self.production_status[producer.tag].unit_type:
                    production_reports.append(f"{self.production_status[producer.tag]} ")
                #pending_unit_type = self.production_line[producer.tag]

                #production_report[producer.tag] = (self.production_line[producer.tag], self.production_status[producer.tag] )
            current_time = time.time()
            if current_time - self.last_report_time > 0.5:
                self.last_report_time = current_time
                if len(production_reports) > 0:
                    if self._debug: self.print(f"===Production Status Report=== ~ | {self.producer_unit_type.name} x {len(self.all_producers_of_type)} | {','.join(production_reports)}")
        
        pass
    def get_creation_ability(self, unit_type):
        ability = self.ai._game_data.units[unit_type.value].creation_ability
        print(f'get_creation_ability<{unit_type}>: id: {ability.id}')
        return ability
    def get_creation_ability(self, unit_type):
        ability = self.ai._game_data.units[unit_type.value].creation_ability
        print(f'get_creation_ability<{unit_type}>: id: {ability.id}')
        return ability
    #utility funcs
    def get_unit_count(self, unit_type) -> int:
        #adapted from sharpy sc2 implementation
        count = 0

        for unit in self.ai.units:
            if self.knowledge.unit_values.real_type(unit.type_id) == unit_type:
                count += 1

        if unit_type == self.knowledge.my_worker_type:
            count = max(count, self.ai.supply_workers)

        ability = self.ai._game_data.units[unit_type.value].creation_ability

        if self.knowledge.my_race == Race.Zerg:
            pending = sum([o.ability.id == ability.id for u in self.cache.own(UnitTypeId.EGG) for o in u.orders])
            if unit_type == UnitTypeId.ZERGLING:
                count += pending * 2
            else:
                count += pending

        if unit_type == self.knowledge.my_worker_type:
            count = max(self.ai.supply_workers, count)

        count += sum([o.ability and o.ability.id == ability.id for u in self.all_producers_of_type for o in u.orders])

        return count
    def get_cost(self, unit_type):
        unit_data = self.ai._game_data.units[unit_type.value]
        cost = self.ai._game_data.calculate_ability_cost(unit_data.creation_ability)
        return cost
    def can_afford(self, unit_type):
        unit_data = self.ai._game_data.units[unit_type.value]
        return self.knowledge.can_afford(unit_data.creation_ability)
    def reserve_resources_for_unit_type(self, unit_type):
       cost = self.get_cost(unit_type)
       self.knowledge.reserve(cost.minerals, cost.vespene)
    def has_requirement(self, req_unit_type):
        return self.get_count(req_unit_type) > 0
    def supply_left(self, supply_left_amount):
        return self.ai.supply_left <= supply_left_amount and self.ai.supply_cap < 200
    def supply_used(self, supply_amount, supply_type):
        if supply_type == SupplyType.All:
            return self.ai.supply_used >= supply_amount
        if supply_type == SupplyType.Combat:
            return self.ai.supply_used - self.ai.supply_workers >= supply_amount
        return self.ai.supply_workers >= supply_amount
    def ready_to_train(self, producer):
        if not producer.is_ready:
            return False
        elif producer.is_attacking:
            return False
        elif producer.is_flying and producer.type_id != UnitTypeId.OVERLORD:
            return False
        elif producer.add_on_tag == 0:
            return len(producer.orders) == 0
        elif producer.has_reactor:
            return len(producer.orders) == 1
        return len(producer.orders) == 0
    async def train_unit(self, producer, unit_type, to_count=99, priority=False):
        if self.ready_to_train(producer):
            unit_count = self.get_unit_count(unit_type)
            if unit_count < to_count:
                if self.can_afford(unit_type):  
                    #self.print(f"{producer} try to train => unit_type: {unit_type} unit_count: {unit_count} / {to_count}")
                    #ability = AbilityId.MORPHTOBANELING_BANELING 
                    if producer.train(unit_type, queue=False, can_afford_check=False):
                        unit_count+= 1
                        self.print(f"\n ~ | {producer} train => unit_type: {unit_type} unit_count: {unit_count} / {to_count}")
                        self.production_status[producer.tag].unit_type = unit_type
                        unit_count+= 1

                        if unit_count < to_count and producer.has_reactor:
                            #if not reached count yet and has reactor
                            if producer.train(unit_type, queue=False, can_afford_check=False):
                                self.print(f"\n ~ | {producer} train => unit_type: {unit_type} unit_count: {unit_count} / {to_count}")
                                unit_count+= 1

                        #pos: [Point2] = self._find_closest_to_target(creep_target, self.creep_map)
                        #return True
                        pass
                else:
                    if priority:
                        #reserve only one
                        self.reserve_resources_for_unit_type(unit_type)
                        return True   
        #return True
        pass

    async def train_units(self,producers, unit_type, target_count=99, priority=False):
        for producer in producers:
            if self.production_status[producer.tag].progress != 0:
                continue
            await self.train_unit(producer, unit_type, target_count, priority)

        return True
    async def manage_producers(self):
        pass
   
            # for unit in self.cache.own(unit_type):
            #     if not unit.is_ready:
            #         percentage = max(percentage, unit.build_progress)
