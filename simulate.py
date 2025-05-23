import random
from abc import ABC, abstractmethod
import csv
import statistics
import copy
from typing import Dict
import math

#region classes
class SimulationDetails:
  """Details about the simulation
  """
  def __init__(self, label: str, multipliers: Dict[int, list[int]]):
    self.label = label
    self.multipliers = multipliers

class SimResultState:
  """The Sim Result Stats
  """
  def __init__(self, points: int = 0, rolls_done: int = 0, initial_dice: int = 0, free_dice: int = 0, gems: int = 0, chroma: int = 0, obsidian: int = 0, otta: int = 0, gold: int = 0):
    self.points = points
    self.rolls_done = rolls_done
    self.initial_dice = initial_dice
    self.free_dice = free_dice
    self.gems = gems
    self.chroma = chroma
    self.obsidian = obsidian
    self.otta = otta
    self.gold = gold

class SimResult:
  """Result of a simulation
  """
  points_breakpoints = [bp + s for s in [0, 20000, 40000, 60000, 80000] for bp in [2000, 5000, 8000, 12000, 16000, 20000]]

  roll_dice_task_breakpoints = [5, 10, 20, 30, 40, 60, 80, 100, 150, 200, 250, 300, 350, 400, 450, 500, 600]
  roll_dice_task_reward = [1, 2, 2, 2, 2, 3, 3, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]

  def __init__(self):
    self.current_state = SimResultState()
    self.saved_state: list[tuple[int, SimResultState]] = []
    self.points_bp_met = -1
    self.roll_dice_bp_met = -1

  def add_points(self, num_points: int):
    """Add points to the result AND get the number of dice we get back from meeting points breakpoints

    Args:
      num_points (int): Number of points to add
    """
    if (num_points <= 0):
      return 0
    
    # add points to result
    self.current_state.points += num_points

    # check if we met any points breakpoints
    num_dice = 0
    for bp in self.points_breakpoints[self.points_bp_met+1:]:
      if (self.current_state.points < bp):
        break
      self.points_bp_met += 1
      num_dice += 2

    self.current_state.free_dice += num_dice
  
  def add_rolls(self, num_rolls: int):
    """Add number of rolls to the result AND get the number of dice we get back from meeting Roll Dice task breakpoints

    Args:
      num_rolls (int): Number of rolls to add
    """
    if (num_rolls <= 0):
      return 0

    # add rolls done to result
    self.current_state.rolls_done += num_rolls

    # ONLY add to initial dice IF we run out of free dice
    if (self.current_state.free_dice <= num_rolls):
      self.current_state.initial_dice += num_rolls - self.current_state.free_dice
    self.current_state.free_dice = max(0, self.current_state.free_dice - num_rolls)

    # check if we meet any task breakpoints
    num_dice = 0
    for bp in self.roll_dice_task_breakpoints[self.roll_dice_bp_met+1:]:
      if (self.current_state.rolls_done < bp):
        break
      self.roll_dice_bp_met += 1
      num_dice = self.roll_dice_task_reward[self.roll_dice_bp_met]

    self.current_state.free_dice += num_dice

  def save(self, current_position):
    """Save the history of state

    Args:
      current_position (int): Current position that we are on
    """
    self.saved_state.append([current_position, copy.deepcopy(self.current_state)])

class Tile(ABC):
  """
  A single tile on the board
  """
  def roll(self, multiplier: int, result: SimResult):
    """Do a dice roll from this tile

    Args:
      multiplier (int): The multiplier applied to this tile
      result (SimResult): The cumulative result of the simulation run that we will add to

    Returns:
      int: The sum of the two dice results
    """
    result.add_rolls(multiplier)
    return random.randint(1, 6) + random.randint(1, 6)

  @abstractmethod
  def get_reward(self, multiplier: int, result: SimResult):
    """Get the reward from landing on a tile

    Args:
      multiplier (int): The multiplier applied to this tile
      result (SimResult): The cumulative result of the simulation run that we will add to
    """    
    pass

  @abstractmethod
  def get_value(self):
    """Get the value of this tile in terms of points AND dice

    Returns:
      tuple[int,int]: Number of points, Number of dice
    """
    pass

class FlatTile(Tile):
  def __init__(self, points: int = 0, gems: int = 0, dice: int = 0):
    """Create a FlatTile that just gives the amount of resource

    Args:
      points (int, optional): Number of points. Defaults to 0.
      gems (int, optional): Number of gems. Defaults to 0.
      dice (int, optional): Number of dice. Defaults to 0.
    """
    self.points = points
    self.gems = gems
    self.dice = dice

  def get_reward(self, multiplier: int, result: SimResult):
    result.add_points(self.points * multiplier)

    result.current_state.gems += (self.gems * multiplier)

    result.current_state.free_dice += (self.dice * multiplier)

  def get_value(self):
    return self.points, self.dice

class GrandPrizeTile(Tile):
  def get_reward(self, multiplier: int, result: SimResult):
    spin = random.randint(1,10000)
    if (spin <= 666): # 2x chroma keys
      result.current_state.chroma += (2 * multiplier)
    elif (spin <= 666 + 2666): # 1x obsidian key
      result.current_state.obsidian += (1 * multiplier)
    elif (spin <= 666 + 2666 + 2666): # 100 gems
      result.current_state.gems += (100 * multiplier)
    elif (spin <= 666 + 2666 + 2666 + 666): # 1x chroma key
      result.current_state.chroma += (1 * multiplier)
    elif (spin <= 666 + 2666 + 2666 + 666 + 666): # 2x dice
      result.current_state.free_dice += (2 * multiplier)
    else: # 1x dice
      result.current_state.free_dice += (1 * multiplier)
  
  def get_value(self):
    return 0, (666 * 2 + 2666 * 1) / 10000

class PointWheelTile(Tile):
  def get_reward(self, multiplier: int, result: SimResult):
    spin = random.randint(1,10000)
    points = 100
    if (spin <= 3478):
      points = 200
    elif (spin <= 3478 + 2608):
      points = 500
    elif (spin <= 3478 + 2608 + 434):
      points = 1000

    spin2 = random.randint(1,10000)
    spin_multiplier = 1
    if (spin2 <= 3076):
      spin_multiplier = 3
    elif (spin2 <= 3076 + 769):
      spin_multiplier = 5

    result.add_points(points * spin_multiplier * multiplier)
  
  def get_value(self):
    # spin points
    point_value = (3478 * 100 + 3478 * 200 + 2608 * 500 + 434 * 1000) / 10000
    # spin multipliers
    point_value *= (6153 * 1 + 3076 * 3 + 769 * 5) / 10000
    return point_value, 0

class FateWheelTile(Tile):
  def get_reward(self, multiplier: int, result: SimResult):
    spin = random.randint(1,10000)
    if (spin <= 2500): # 100 points
      result.add_points(500 * multiplier)
    elif (spin <= 2500 + 300): # 2x otta
      result.current_state.otta += (2 * multiplier)
    elif (spin <= 2500 + 300 + 700): # 1x chroma key
      result.current_state.chroma += (1 * multiplier)
    elif (spin <= 2500 + 300 + 700 + 1500): # 1x dice
      result.current_state.free_dice += (1 * multiplier)
    else: # 2000 gold
      result.current_state.gold += (2000 * multiplier)
  
  def get_value(self):
    return (500 * 2500) / 10000, (1500 * 1) / 10000
#endregion classes

#region helpers
def calc_best_multipliers(board: list[Tile], multiplier: int):
  """Calculate the best multipliers for the board

  Args:
    board (list[Tile]): The board
    multiplier (int): The multiplier to set around the board

  Returns:
    list[int]: The best multipliers to apply when rolling from each tile of the board
  """
  tile_values: list[tuple[float,float]] = [tile.get_value() for tile in board]
  #dice value = average points gained per die / (1 - average die gained per die)
  dice_value = statistics.fmean([v[0] for v in tile_values]) / (1 - statistics.fmean([v[1] for v in tile_values]))
  # calculated value of tiles in terms of points with NO APPLIED MULTIPLIERS
  tile_calc_values = [v[0] + v[1]*dice_value for v in tile_values]
  # get the total point value of each tile based on what tiles can be reached from it
  def get_values(index: int, num_hits: int):
    points = tile_values[index][0] * num_hits / 36
    dice = tile_values[index][1] * num_hits / 36
    value = tile_calc_values[index] * num_hits / 36
    return points, dice, value
  tile_mult_value: list[tuple[float, float, float]] = []
  for i in range(len(tile_calc_values)):
    total_points = 0
    total_dice = 0
    total_value = 0
    # 2 → 1 way: (1+1)
    points, dice, value = get_values((i + 2) % 24, 1)
    total_points += points
    total_dice += dice
    total_value += value
    # 3 → 2 ways: (1+2, 2+1)
    points, dice, value = get_values((i + 3) % 24, 2)
    total_points += points
    total_dice += dice
    total_value += value
    # 4 → 3 ways: (1+3, 2+2, 3+1)
    points, dice, value = get_values((i + 4) % 24, 3)
    total_points += points
    total_dice += dice
    total_value += value
    # 5 → 4 ways: (1+4, 2+3, 3+2, 4+1)
    points, dice, value = get_values((i + 5) % 24, 4)
    total_points += points
    total_dice += dice
    total_value += value
    # 6 → 5 ways: (1+5, 2+4, 3+3, 4+2, 5+1)
    points, dice, value = get_values((i + 6) % 24, 5)
    total_points += points
    total_dice += dice
    total_value += value
    # 7 → 6 ways: (1+6, 2+5, 3+4, 4+3, 5+2, 6+1)
    points, dice, value = get_values((i + 7) % 24, 6)
    total_points += points
    total_dice += dice
    total_value += value
    # 8 → 5 ways: (2+6, 3+5, 4+4, 5+3, 6+2)
    points, dice, value = get_values((i + 8) % 24, 5)
    total_points += points
    total_dice += dice
    total_value += value
    # 9 → 4 ways: (3+6, 4+5, 5+4, 6+3)
    points, dice, value = get_values((i + 9) % 24, 4)
    total_points += points
    total_dice += dice
    total_value += value
    # 10 → 3 ways: (4+6, 5+5, 6+4)
    points, dice, value = get_values((i + 10) % 24, 3)
    total_points += points
    total_dice += dice
    total_value += value
    # 11 → 2 ways: (5+6, 6+5)
    points, dice, value = get_values((i + 11) % 24, 2)
    total_points += points
    total_dice += dice
    total_value += value
    # 12 → 1 way: (6+6)
    points, dice, value = get_values((i + 12) % 24, 1)
    total_points += points
    total_dice += dice
    total_value += value

    tile_mult_value.append(tuple([total_points, total_dice, total_value]))

  # sort the indices of the tile_mult_value such that the values are in descending order
  sorted_index = sorted(range(len(tile_mult_value)), key=lambda i: tile_mult_value[i][2], reverse=True)

  best_multiplier = [1] * 24
  best_ppd = sum([best_multiplier[i] * tile_mult_value[i][2] for i in range(len(best_multiplier))]) / sum(best_multiplier)
  for i in range(len(sorted_index)):
    best_multiplier[sorted_index[i]] = multiplier

    # Average Projected Dice Value = Sum(PDVxM) / Sum(Tile Multipliers)
    avg_num_dice = sum([best_multiplier[j] * tile_mult_value[j][1] for j in range(len(best_multiplier))]) / sum(best_multiplier)
    # PPID = Sum(Project Points Value of Tile * Tile Multiplier) / Sum(Tile Multipliers) / (1 - Average Projected Dice Value)
    ppd = sum([best_multiplier[j] * tile_mult_value[j][0] for j in range(len(best_multiplier))]) / sum(best_multiplier) / (1 - avg_num_dice)
    if (ppd < best_ppd):
      best_multiplier[sorted_index[i]] = 1
      break
    best_ppd = ppd
  return best_multiplier

averages_output = '''Averages:
- Number of points earned: {points:,}
- Number of dice needed initially: {initial_dice:,}
- Points per initial dice: {ppid:,}
- Number of rolls overall: {rolls:,}
- Points per roll: {ppd:,}
- Extra dice gotten: {free_dice:,}
- Gems gotten: {gems:,}
- Chroma keys gotten: {chroma:,}
- Obsidian keys gotten: {obsidian:,}
- Otta shards gotten: {otta:,}
- Gold gotten: {gold:,}
'''
def output_stats(runs: list[SimResult]):
  """Output the stats of all the runs

  Args:
    runs (list[SimResult]): The simulation runs
  """
  num_rounds = len(runs)
  total_points = 0
  total_rolls_done = 0
  total_initial_dice = 0
  total_free_dice = 0
  total_gems = 0
  total_chroma = 0
  total_obsidian = 0
  total_otta = 0
  total_gold = 0
  tiles_hit_freq = [0] * 24
  for i in range(num_rounds):
    run = runs[i]
    total_points += run.current_state.points
    total_rolls_done += run.current_state.rolls_done
    total_initial_dice += run.current_state.initial_dice
    total_free_dice += run.current_state.free_dice
    total_gems += run.current_state.gems
    total_chroma += run.current_state.chroma
    total_obsidian += run.current_state.obsidian
    total_otta += run.current_state.otta
    total_gold += run.current_state.gold
    for state in run.saved_state:
      tiles_hit_freq[state[0]] += 1
  
  avg_points = total_points / num_rounds
  avg_initial_dice = total_initial_dice / num_rounds
  avg_free_dice = total_free_dice / num_rounds
  avg_rolls = total_rolls_done / num_rounds
  print(averages_output.format(
    points=avg_points,
    initial_dice=avg_initial_dice,
    ppid=avg_points / (avg_initial_dice - avg_free_dice),
    rolls=avg_rolls,
    ppd=avg_points / avg_rolls,
    free_dice=avg_free_dice,
    gems=total_gems / num_rounds,
    chroma=total_chroma / num_rounds,
    obsidian=total_obsidian / num_rounds,
    otta=total_otta / num_rounds,
    gold=total_gold / num_rounds
  ))
  for i in range(len(tiles_hit_freq)):
    tiles_hit_freq[i] /= num_rounds
  print(f'Tiles hit frequencies: {tiles_hit_freq}')

def output_csv(csv_file_name: str, runs: list[SimResult]):
  header = ['# of Points', '# of Dice Initially', 'Points per Initial Dice', '# of Rolls Done', 'Points per Roll', '# of Gems', '# of Chroma Keys', '# of Obsidian Keys', '# of Otta Shards', '# of Gold']
  with open(f'generated/{csv_file_name}', 'w', newline='') as csvfile:
      csvwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
      csvwriter.writerow(header)
      for run in runs:
        row = [
          run.current_state.points,
          run.current_state.initial_dice,
          run.current_state.points / run.current_state.initial_dice,
          run.current_state.rolls_done,
          run.current_state.points / run.current_state.rolls_done,
          run.current_state.gems,
          run.current_state.chroma,
          run.current_state.obsidian,
          run.current_state.otta,
          run.current_state.gold
        ]
        csvwriter.writerow(row)

def create_sim_details_same_mult(label: str, multipliers: list[int]):
  """Create a SimulationDetails with the same multiplier map at every level

  Args:
      label (str): label for SimulationDetails
      multipliers (list[int]): multiplier map to apply

  Returns:
      SimulationDetails: The SimulationDetails
  """
  return SimulationDetails(label, {
    2: multipliers,
    3: multipliers,
    5: multipliers,
    10: multipliers,
  })
#endregion helpers

def simulate_single_run(board: list[Tile], multipliers: Dict[int,list[int]], num_dice_rolls: int, points_to_meet: int, save_history: bool = False):
  """Simulate going around the board starting with a specified number of dice rolls

  Args:
    board (list[Tile]): The board
    multipliers (Dict[int,list[int]]): The multipliers to apply when rolling from each tile
    num_dice_rolls (int): Number of dice to start with. The sim will stop if all of these dice are used.
    points_to_meet (int): Number of points to aim for. The sim will stop if we reach this threshold even if we didn't use all starting dice.
    save_history (bool): Whether we should save the state of run after every single roll. Will slow down sim.

  Returns:
    SimResult: Result of simulation
  """
  result = SimResult()
  current_position = 0
  while (result.current_state.points < points_to_meet and (result.current_state.initial_dice < num_dice_rolls or result.current_state.free_dice > 0)) :
    # get multiplier then check if it's allowed
    num_turns = num_dice_rolls - result.current_state.initial_dice + result.current_state.free_dice
    list_of_multipliers = [ 1 ] * 24
    if (num_turns >= 100):
      list_of_multipliers = multipliers[10]
    elif (num_turns >= 50):
      list_of_multipliers = multipliers[5]
    elif (num_turns >= 30):
      list_of_multipliers = multipliers[3]
    elif (num_turns >= 20):
      list_of_multipliers = multipliers[2]
    multiplier = list_of_multipliers[current_position]
    if (num_turns < 20):
      multiplier = min(1, multiplier)
    elif (num_turns < 30):
      multiplier = min(2, multiplier)
    elif (num_turns < 50):
      multiplier = min(3, multiplier)
    elif (num_turns < 100):
      multiplier = min(5, multiplier)

    # roll the dice
    old_tile = board[current_position]
    roll = old_tile.roll(multiplier, result)

    # land on new tile and get the reward
    current_position = (current_position + roll) % 24
    tile = board[current_position]
    tile.get_reward(multiplier, result)

    # save history
    if (save_history):
      result.save(current_position)
  
  return result

def simulation(sim_details: list[SimulationDetails], board: list[Tile], num_rounds: int, num_dices: list[int], points_to_meet: int, csv: bool = False, save_history: bool = False):
  """Run simulations to get the average PPID using a specified number of starting dice. A single run will only end after all starting dice and free dice received in the run are used.

  Args:
    sim_details (list[SimulationDetails]): List of multipliers to run
    board (list[Tile]): The board
    num_rounds (int): The number of times to run simulation
    num_dices (list[int]): List of the number of dice to start each simulation with
    points_to_meet (int): Number of points to aim for. The sim will stop if we reach this threshold even if we didn't use all starting dice.
    output_csv (bool): Whether we should output the runs in a CSV
    save_history (bool): Whether we should save the state of run after every single roll. Will slow down sim.
  """
  for sim in sim_details:
    runs = []
    print(sim.label)
    for dices in num_dices:
      print('Simulation of {:,} players starting with {:,} dice each trying to reach {:,} points:'.format(num_rounds, dices, points_to_meet))
      print('Applied Multipliers: {}'.format(sim.multipliers))
      for i in range(num_rounds):
        runs.append(simulate_single_run(board, sim.multipliers, dices, points_to_meet, save_history))
        if (i % 10000 == 9999):
          print(f'{i+1} sims done')
      output_stats(runs)
    if (csv):
      output_csv(f'{sim.label}.csv', runs)

board = [
  FlatTile(points=400),
  FlatTile(gems=50),
  FlatTile(points=50),
  FlatTile(points=400),
  FlatTile(points=800),
  FlatTile(points=50),
  FlatTile(dice=2),
  FlatTile(gems=50),
  GrandPrizeTile(),
  FlatTile(),           # GREEN PRESENT
  PointWheelTile(),
  FlatTile(points=50),
  FlatTile(points=200),
  FlatTile(),           # GREEN PRESENT
  FlatTile(dice=2),
  FlatTile(points=200),
  FlatTile(points=800),
  FlatTile(),           # GREEN PRESENT
  FlatTile(points=50),
  FlatTile(points=200),
  PointWheelTile(),
  FlatTile(),           # GREEN PRESENT
  FateWheelTile(),
  FlatTile(points=200),
]

sims = [
  SimulationDetails('BestMultipliers', {
    2: calc_best_multipliers(board,2),
    3: calc_best_multipliers(board,3),
    5: calc_best_multipliers(board,5),
    10: calc_best_multipliers(board,10)
  }),
  create_sim_details_same_mult('6x10', [ 1, 1, 1, 1, 1, 1, 1, 10, 10, 10, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 10, 10, 10, 1 ]),
  create_sim_details_same_mult('5x10', [ 1, 1, 1, 1, 1, 1, 1, 1, 10, 10, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 10, 10, 10, 1 ]),
]

# def fiery_sim():
#   def get_stats(runs: list[SimResult], points_to_meet: int):
#     num_rounds = len(runs)
#     total_points = 0
#     total_initial_dice = 0
#     total_free_dice = 0
#     num_over_threshold = 0
#     for i in range(num_rounds):
#       run = runs[i]
#       if (run.current_state.points >= points_to_meet):
#         num_over_threshold += 1
#       total_points += run.current_state.points
#       total_initial_dice += run.current_state.initial_dice
#       total_free_dice += run.current_state.free_dice
    
#     avg_points = total_points / num_rounds
#     avg_initial_dice = total_initial_dice / num_rounds
#     avg_free_dice = total_free_dice / num_rounds
#     ppid = avg_points / (avg_initial_dice - avg_free_dice)
#     return num_over_threshold, ppid

#   def compile_stats(sim_results: list[int, int, tuple[list[int], int, int]]):
#     winning_count = 0
#     winners = []
#     for i in range(len(sim_results)):
#       map_stats = sim_results[i]
#       if (map_stats[3] > winning_count):
#         winning_count = map_stats[3]
#         winners = [{ 'multipliers': map_stats[2], 'ppid': map_stats[4] }]
#       elif (map_stats[3] == winning_count):
#         winners.append({ 'multipliers': map_stats[2], 'ppid': map_stats[4] })
#     return winning_count, winners

#   def create_maps():
#     map_template = [False, False, False, False, False, False, False, True, True, True, False, False, False, False, False, False, False, False, False, False, True, True, True, False]
#     maps = []
#     def traverse(maps: list[list[int]], index: int, map_to_build: list[int]):
#       if (index == len(map_template)):
#         maps.append(map_to_build)
#         return
#       if (not map_template[index]):
#         map_to_build.append(1)
#         traverse(maps, index+1, map_to_build)
#       else:
#         map1 = map_to_build.copy()
#         map1.append(1)
#         traverse(maps, index+1, map1)
#         map2 = map_to_build.copy()
#         map2.append(2)
#         traverse(maps, index+1, map2)
#         map3 = map_to_build.copy()
#         map3.append(3)
#         traverse(maps, index+1, map3)
#         map5 = map_to_build.copy()
#         map5.append(5)
#         traverse(maps, index+1, map5)
#     traverse(maps, 0, [])
#     sim_maps = list(map(create_sim_details_same_mult, [f'map{i}' for i in range(len(maps))], maps))
#     return sim_maps
#   maps = create_maps()

#   sims = {
#     20_000: {
#       "dices": [10 * i for i in range(5,11)],
#       "maps": maps
#     },
#     40_000: {
#       "dices": [10 * i for i in range(11,19)],
#       "maps": maps
#     },
#   }

#   all_results = []
#   all_compiled_results = {}
#   for points_to_meet in sims.keys():
#     compiled_results = {}
#     for dices in sims[points_to_meet]["dices"]:
#       num_sims = len(sims[points_to_meet]["maps"])
#       results = []
#       count = 0
#       print(f'Simulation of 10,000 players starting with {dices:,} dice each trying to reach {points_to_meet:,} points:')
#       for sim in sims[points_to_meet]["maps"]:
#         map_runs = []
#         for i in range(10_000):
#           map_runs.append(simulate_single_run(board, sim.multipliers, dices, math.inf))
#         num_over_thresold, ppid = get_stats(map_runs, points_to_meet)
#         results.append([points_to_meet, dices, sim.multipliers[2], num_over_thresold, ppid])
#         count += 1
#         print(f'{points_to_meet:,} points {dices} dices: {count}/{num_sims} sims complete')
#       all_results += results
#       winning_count, best_results = compile_stats(results)
#       compiled_results[dices] = {
#         'success rate': winning_count/10_000*100,
#         'results': best_results
#       }
#     all_compiled_results[points_to_meet] = compiled_results
#   print(all_compiled_results)
#   def output_results_into_csv():
#     header = ['# of Points', '# of Dice Initially', 'Multiplier Map', 'Success Rate', 'PPID']
#     with open('fiery_wind.csv', 'w', newline='') as csvfile:
#         csvwriter = csv.writer(csvfile)
#         csvwriter.writerow(header)
#         for result in all_results:
#           row = [
#             result[0],
#             result[1],
#             result[2],
#             result[3] / 10_000 * 100,
#             result[4]
#           ]
#           csvwriter.writerow(row)
#   output_results_into_csv()
