import numpy as np
from scipy.spatial import KDTree, distance_matrix
from sc2.position import Point2
from sc2.unit import Unit
from sharpy.general.extended_power import ExtendedPower
from sc2.units import Units
from .mew_expand import ExpansionBase

class NydusSolver:
    def __init__(self, game_info, ai):
        self.game_info = game_info
        self.ai = ai
        self.standin = [(x, y) for x in range(game_info.pathing_grid.width) for y in range(game_info.pathing_grid.height)]
        self.tree = KDTree(self.standin)

    def find_enemy_gases(self, target_location, radius=12, exclusion_radius=11.5):
        enemy_gases = self.ai.vespene_geyser.closer_than(radius, target_location)
        gas_positions = [gas.position for gas in enemy_gases]
        gas_indices = [self.tree.query_ball_point(gas_position, exclusion_radius) for gas_position in gas_positions]
        close_to_gas = set([idx for sublist in gas_indices for idx in sublist])
        return close_to_gas

    def find_target_pathable(self, target_location, search_radius=45):
        target_height = self.game_info.terrain_height[target_location.rounded]
        target_pathable = [
            self.standin[z]
            for z in self.tree.query_ball_point(target_location, search_radius)
            if self.game_info.terrain_height[self.standin[z]] == target_height
            and self.game_info.pathing_grid[self.standin[z]] == 1
        ]
        return target_pathable

    def find_close_to_ramp(self, ramp_location, radius=18):
        close_to_ramp = [
            self.standin[z]
            for z in self.tree.query_ball_point(ramp_location, radius)
        ]
        return close_to_ramp

    def find_away_from_gas_and_ramp(self, target_pathable, close_to_gas, close_to_ramp):
        away_from_gas_and_ramp = list(set(target_pathable) - close_to_gas - set(close_to_ramp))
        return away_from_gas_and_ramp

    def calculate_distances(self, locations, target_location):
        distances = distance_matrix(
            [Point2(pos) for pos in locations],
            [target_location]
        )
        return distances

    def calculate_nydus_spots(self, num_spots):
        game_info = self.game_info
        ai = self.ai

        # Get the height of the enemy main to make sure we find the right tiles
        enemy_main_base_location = ai.enemy_start_locations[0].rounded
        enemy_height = game_info.terrain_height[enemy_main_base_location]

        # Find gases and remove points close to them
        close_to_gas = self.find_enemy_gases(enemy_main_base_location)

        # Find the enemy main base pathable locations
        enemy_main = self.find_target_pathable(enemy_main_base_location)

        # Find the enemy ramp so we can avoid it
        close_to_ramp = self.find_close_to_ramp(ai.enemy_start_locations[0])

        # Main base, but without points close to the ramp or gases
        main_away_from_gas_and_ramp = self.find_away_from_gas_and_ramp(enemy_main, close_to_gas, close_to_ramp)

        # Get a matrix of the distances from the points to the enemy main
        distances = self.calculate_distances(main_away_from_gas_and_ramp, enemy_main_base_location)

        # Select the point with the greatest distance from the enemy main
        #optimal_nydus_index = np.argmax(distances[:, 0])

        #optimal_nydus_location = Point2(main_away_from_gas_and_ramp[optimal_nydus_index])
        optimal_nydus_location = Point2(main_away_from_gas_and_ramp[np.where(distances == max(distances))[0][0]])

        # Get other positions in the enemy main for potential follow-up Nyduses
        possible_nydus_locations = np.array(main_away_from_gas_and_ramp)[np.where(distances[:, 0] > 13)[0]]
        edge = [
            Point2(loc)
            for loc in possible_nydus_locations
            if not all([game_info.pathing_grid[Point2(loc).offset(Point2(d)).rounded] == 1 for d in Point2((0, 1)).neighbors8])
        ]

        nydus_locations = edge[:num_spots]
        
        return optimal_nydus_location, nydus_locations

    def calculate_defensive_nydus_spots(self, num_spots):
        ai = self.ai

        # Friendly main base location
        friendly_main_base_location = ai.start_location.rounded

        # Get all player expansion bases from the registry
        player_expansion_bases = [base for base in ExpansionBase.Registry.values() if base.is_ours]

        # Initialize lists to store selected points and their distances to the main base
        selected_points = []
        distances_to_main_base = []

        # Iterate over enemy expansion bases
        for player_expo_base in player_expansion_bases:
            if player_expo_base:
                # Enemy expansion base location
                player_expo_location = player_expo_base.center_location

                # Find gases and remove points close to them
                close_to_gas = self.find_enemy_gases(player_expo_location)

                # Find the enemy main base pathable locations
                player_main = self.find_target_pathable(player_expo_location)

                # Find the enemy ramp so we can avoid it
                close_to_ramp = self.find_close_to_ramp(player_expo_location)

                # Main base, but without points close to the ramp or gases
                main_away_from_gas_and_ramp = self.find_away_from_gas_and_ramp(player_main, close_to_gas, close_to_ramp)

                # Calculate distances to the friendly main base
                distances = self.calculate_distances(main_away_from_gas_and_ramp, friendly_main_base_location)

                # Find the closest pathable location to the friendly main base
                closest_index = np.argmin(distances[:, 0])
                #farthest_point_index = np.argmax(distances[:, 0])
                #farthest_point = main_away_from_gas_and_ramp[farthest_point_index]
                closest_point = main_away_from_gas_and_ramp[closest_index]

                # Store the selected point and its distance to the main base
                selected_points.append(closest_point)
                distances_to_main_base.append(distances[closest_index, 0])

        # Filter out points that are on ramps
        non_ramp_points = []
        for point, distance in zip(selected_points, distances_to_main_base):
            if point not in close_to_ramp:
                non_ramp_points.append((point, distance))

        # Sort the non-ramp points by distance to the main base
        non_ramp_points.sort(key=lambda x: x[1], reverse=True)

        # Select the desired number of defensive nydus spots
        defensive_nydus_spots = [Point2(point) for point, _ in non_ramp_points[:num_spots]]


        return defensive_nydus_spots


    def calculate_offensive_nydus_spots(self, num_spots):
        ai = self.ai

        # Get all enemy expansion bases from the registry
        enemy_expansion_bases = [base for base in ExpansionBase.Registry.values() if not base.is_ours]

        # Initialize lists to store selected points and their indices
        selected_points = []
        distances_to_main_base = []

        for enemy_expo_base in enemy_expansion_bases:
            if enemy_expo_base:
                # Enemy expansion base location
                enemy_expo_location = enemy_expo_base.center_location
                if enemy_expo_location:

                    # Find gases and remove points close to them
                    close_to_gas = self.find_enemy_gases(enemy_expo_location)

                    # Find the enemy main base pathable locations
                    enemy_main = self.find_target_pathable(enemy_expo_location)

                    # Find the enemy ramp so we can avoid it
                    close_to_ramp = self.find_close_to_ramp(enemy_expo_location)

                    # Main base, but without points close to the ramp or gases
                    main_away_from_gas_and_ramp = self.find_away_from_gas_and_ramp(enemy_main, close_to_gas, close_to_ramp)

                    # Get a matrix of the distances from the points to the enemy main
                    distances = self.calculate_distances(main_away_from_gas_and_ramp, enemy_expo_location)

                    # Select the farthest point from the enemy main base first
                    farthest_point_index = np.argmax(distances[:, 0])
                    #selected_indices.append(farthest_point_index)
                    selected_points.append(main_away_from_gas_and_ramp[farthest_point_index])

                    distances_to_main_base.append(distances[farthest_point_index, 0])

                    # Sort selected points based on distances to the main base (from closest to furthest)
        sorted_indices = np.argsort(distances_to_main_base)[::-1]
        sorted_points = [selected_points[i] for i in sorted_indices]

        # Select the desired number of defensive nydus spots
        offensive_nydus_spots = [Point2(point) for point in sorted_points[:num_spots]]


        return offensive_nydus_spots




# Example usage
def main():
    game_info = get_game_info()  # Placeholder function to get the current game info
    ai = get_ai_instance()  # Placeholder function to get the AI instance

    solver = NydusSolver(game_info, ai)
    solver.calculate_nydus_spots()



    print("Optimal Nydus Location:")
    print(solver.optimal_nydus_location)

    print("Possible Nydus Locations:")
    for loc in solver.nydus_locations:
        print(loc)

    defensive_spots = solver.calculate_defensive_nydus_spots(3)
    print("Defensive Nydus Spots:")
    for spot in defensive_spots:
        print(spot)

    offensive_spots = solver.calculate_offensive_nydus_spots(3)
    print("Offensive Nydus Spots:")
    for spot in offensive_spots:
        print(spot)


