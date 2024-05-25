 from typing import Dict, Set
# from sc2.position import Point2, Point3
# from sc2.ids.ability_id import AbilityId
# from sc2.ids.unit_typeid import UnitTypeId
# from sc2.dicts.unit_train_build_abilities import TRAIN_INFO
# from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
# from sc2.dicts.unit_abilities import UNIT_ABILITIES

# def _format_unit_type_id(unit_type: UnitTypeId) -> str:
#     return f"UnitTypeId: {unit_type.name} id: {unit_type.value}"

# def _format_ability_id(ability: AbilityId) -> str:
#     return f"AbilityId: {ability.name} id: {ability.value}"

# def _get_unit_trained_from(unit_type: UnitTypeId) -> UnitTypeId:
#     producer_unit_type = UNIT_TRAINED_FROM[unit_type]
#     if producer_unit_type:
#         if isinstance(producer_unit_type, (set, Set)):
#             return list(producer_unit_type)[0]  # Convert set to list and return the first element
#     return producer_unit_type

# def _get_train_ability_id(unit_type: UnitTypeId) -> AbilityId:
#     producer_unit_type = _get_unit_trained_from(unit_type)
#     return TRAIN_INFO[producer_unit_type][unit_type]['ability']

# def _get_abilities(unit_type: UnitTypeId) -> Set[AbilityId]:
#     return UNIT_ABILITIES[unit_type]

# def evaluate_unit_data(unit_type: UnitTypeId) -> str:
#     output = []

#     formatted_unit_type = _format_unit_type_id(unit_type)
#     width = len(f"Evaluate Unit Data: {formatted_unit_type}")
#     output.append(f"\n ~ ╔{'═' * (width-3)}")
#     output.append(f"\n ~ ║ Evaluate Unit Data: {formatted_unit_type}")
#     output.append(f"\n ~ ║ evaluate_unit_data for unit: {formatted_unit_type}")

#     producer_unit_type = _get_unit_trained_from(unit_type)
#     train_ability = _get_train_ability_id(unit_type)

#     output.append(f"\n ~ ║ producer unit: { _format_unit_type_id(producer_unit_type)}")
#     output.append(f"\n ~ ║ creation ability: { _format_ability_id(train_ability)}")

#     output.append(f"\n ~ ╠{'-' * (width-3)}")

#     abilities = _get_abilities(unit_type)
#     if abilities:
#         output.append(f"\n ~ ║ unit: {formatted_unit_type} has abilities: ")
#         output.append(f"\n ~ ╠{'-' * (width-3)}")
#         for i, ability in enumerate(abilities):
#             output.append(f"\n ~ ║  [{i}]: {_format_ability_id(ability)}")

#     output.append(f"\n ~ ╚{'═' * (width-3)}")
#     return '\n ~ ║'.join(output)

# def log_evaluate_unit_data(unit_type: UnitTypeId) -> None:
#     print(evaluate_unit_data(unit_type))

# def draw_text_on_world(ai, pos: Point2, text: str, draw_color=(255, 102, 255), font_size=14) -> None:
#     z_height: float = ai.get_terrain_z_height(pos)
#     ai.client.debug_text_world(
#         text,
#         Point3((pos.x, pos.y, z_height)),
#         color=draw_color,
#         size=font_size,
#     )

# def draw_point_on_world(ai, pos: Point2, draw_color=(70, 255, 70)) -> None:
#     z_height: float = ai.get_terrain_z_height(pos)
#     ai.client.debug_sphere_out(
#         Point3((pos.x, pos.y, z_height)), 
#         0.5, color=draw_color
#     )

# def draw_aoe_on_world(ai, pos: Point2, radius=2, draw_color=(255, 120, 120)) -> None:
#     z_height: float = ai.get_terrain_z_height(pos)
#     ai.client.debug_sphere_out(
#         Point3((pos.x, pos.y, z_height)), 
#         radius, color=draw_color
#     )
