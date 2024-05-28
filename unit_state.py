from typing import List, Optional, Union, Dict, Set
from sc2.position import Point2, Point3, Pointlike
from sharpy.combat import MicroStep, Action, MoveType
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.buff_id import BuffId
from sc2.data import Race
from sc2.unit import Unit
from sharpy.general.extended_power import ExtendedPower
from sc2.units import Units
from sharpy.combat.group_combat_manager import GroupCombatManager
from sharpy.combat import GenericMicro, Action, CombatUnits, MicroRules
from sharpy.interfaces.combat_manager import MoveType, retreat_move_types
from sharpy.plans.zerg import *

class UnitState:
    previous_unit_states: Dict[int, "UnitState"] = {}

    def __init__(self, position: Point2, velocity: Point2, frame: int, unit_type: int, vitality_percentage: float):
        self.position = position
        self.velocity = velocity
        self.frame = frame
        self.unit_type = unit_type
        self.vitality_percentage = vitality_percentage
        self.last_attacker_tag = None

    @classmethod
    def calculate_velocity(cls, unit: Unit, current_frame: int) -> Point2:
        if unit.tag not in cls.previous_unit_states:
            return Point2((0.0, 0.0))

        previous_state = cls.previous_unit_states[unit.tag]
        if current_frame == previous_state.frame:
            return Point2((0.0, 0.0))

        delta_frame = current_frame - previous_state.frame
        current_position = unit.position
        previous_position = previous_state.position

        velocity = (current_position - previous_position).normalized * unit.distance_per_step * delta_frame
        return velocity#(velocity + previous_state.velocity) * 0.5

    @classmethod
    def calc_unit_vitality_percentage(cls, unit: Unit) -> float:
        if unit.health_percentage > 0:
            # Calculate unit's total health percentage including shields if applicable
            total_health = unit.health_percentage
            if unit.shield_max > 0:
                total_health += unit.shield_percentage / 2.0
            return total_health
        else:
            return 0.0

    @classmethod
    def update_unit_state(cls, unit: Unit, current_frame: int):
        if unit:
            vitality_percentage = cls.calc_unit_vitality_percentage(unit)
            if unit.tag not in cls.previous_unit_states:
                cls.previous_unit_states[unit.tag] = UnitState(unit.position, Point2((0.0, 0.0)), current_frame, unit.type_id, vitality_percentage)
            else:
                previous_state = cls.previous_unit_states[unit.tag]
                if unit.position != previous_state.position:
                    new_velocity = cls.calculate_velocity(unit, current_frame)
                    cls.previous_unit_states[unit.tag] = UnitState(unit.position, new_velocity, current_frame, unit.type_id, vitality_percentage)

            
    @classmethod
    def update_last_attacker(cls, unit, last_attacker_tag: int):
        if unit.tag in cls.previous_unit_states:
            cls.previous_unit_states[unit.tag].last_attacker_tag = last_attacker_tag

    @classmethod
    def predict_target_position(cls, unit: Unit, time_to_impact: float=None) -> Point2:
        if unit.tag in cls.previous_unit_states:
            previous_state = cls.previous_unit_states[unit.tag]
            current_position = Point2((unit.position.x, unit.position.y))
            if time_to_impact is None:
                time_to_impact = unit._bot_object.client.game_step * 22.4
            predicted_position = current_position + previous_state.velocity * time_to_impact
            return Point2((predicted_position.x, predicted_position.y))
        return Point2((unit.position.x, unit.position.y))

