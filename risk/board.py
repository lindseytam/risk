import os
import random
from collections import namedtuple


import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path

import risk.definitions
from collections import deque
from queue import PriorityQueue

Territory = namedtuple('Territory', ['territory_id', 'player_id', 'armies'])
Move = namedtuple('Attack', ['from_territory_id', 'from_armies', 'to_territory_id', 'to_player_id', 'to_armies'])


class Board(object):
    """
    The Board object keeps track of all armies situated on the Risk
    world map. Through the definitions it knows the locations of and
    connections between all territories. It handles ownership, attacks
    and movements of armies.

    Args:
        data (list): a sorted list of tuples describing the state of the
            board, each containing three values:
            - tid (int): the territory id of a territory,
            - pid (int): the player id of the owner of the territory,
            - n_armies (int): the number of armies on the territory.
            The list is sorted by the tid, and should be complete.
    """

    def __init__(self, data):
        self.data = data

    @classmethod
    def create(cls, n_players):
        """
        Create a Board and randomly allocate the territories. Place one army on each territory.
        
        Args:
            n_players (int): Number of players.
                
        Returns:
            Board: A board with territories randomly allocated to the players.
        """
        allocation = (list(range(n_players)) * 42)[0:42]
        random.shuffle(allocation)
        return cls([Territory(territory_id=tid, player_id=pid, armies=1) for tid, pid in enumerate(allocation)])

    # ====================== #
    # == Neighbor Methods == #
    # ====================== #   

    def neighbors(self, territory_id):
        """
        Create a generator of all territories neighboring a given territory.
            
        Args:
            territory_id (int): ID of the territory to find neighbors of.

        Returns:
            generator: Generator of Territories.
        """
        neighbor_ids = risk.definitions.territory_neighbors[territory_id]
        return neighbor_ids
        #return (t for t in self.data if t.territory_id in neighbor_ids)

    def hostile_neighbors(self, territory_id):
        """
        Create a generator of all territories neighboring a given territory, of which
        the owner is not the same as the owner of the original territory.
            
        Args:
            territory_id (int): ID of the territory.
                
        Returns:
            generator: Generator of Territories.
        """
        hostile_neighbors=[]
        player_id = self.owner(territory_id)
        neighbor_ids = risk.definitions.territory_neighbors[territory_id]
        for neighbor in neighbor_ids:
            if self.owner(neighbor) != player_id:
                hostile_neighbors.append(neighbor)
        return hostile_neighbors

    def friendly_neighbors(self, territory_id):
        """
        Create a generator of all territories neighboring a given territory, of which
        the owner is the same as the owner of the original territory.

        Args:
            territory_id (int): ID of the territory.

        Returns:
            generator: Generator of tuples of the form (territory_id, player_id, armies).
        """
        friendlies = []

        player_id = self.owner(territory_id)
        neighbor_ids = risk.definitions.territory_neighbors[territory_id]
        for neighbor in neighbor_ids:
            if self.owner(neighbor) == player_id:
                friendlies.append(neighbor)
        return friendlies
        # return (t for t in self.data if (t.player_id == player_id and t.territory_id in neighbor_ids))

    
    # ================== #
    # == Path Methods == #
    # ================== #

    def is_valid_path(self, path):
        '''
        A path is list of territories satisfying two conditions:
        1. For all territories V in the list (except the last one), the next territory W is in the neighbors if V.
        2. No territory is repeated multiple times.
        3. Valid paths can be of any length (including 0 and 1).

        Args:
            path ([int]): a list of territory_ids which represent the path

        Returns:
            bool: True if the input path is valid
        '''

        # checks for condition 3
        if len(path) == 1 or len(path) == 0:

            return True

        # checks for condition 2
        elif len(path) != len(set(path)):
            return False

        else:
            for i in range(len(path)-1):

                cur_country=path[i]
                next_country=path[i+1]
                if next_country not in risk.definitions.territory_neighbors[cur_country]:
                    return False
            return True

    
    def is_valid_attack_path(self, path):
        '''
        The rules of Risk state that when attacking, 
        a player's armies cannot move through territories they already occupy;
        they must move through enemy territories.
        All valid attacks, therefore, will follow a path of starting on one player's territory and moving trough enemy territories.

        0. Formally, an attack path is a valid path satisfying the following two additional properties:
        1. An attack path must contain at least two territories;
        2. If the first territory is owned by player A, then no other territories in the path are also owned by A.

        Args:
            path ([int]): a list of territory_ids which represent the path

        Returns:
            bool: True if the path is an attack path
        '''

        if len(path) < 2 or not self.is_valid_path(path):
            return False

        else:
            player_id = self.owner(path[0])
            for country in path:
                if path[0] != country and self.owner(country) == player_id:
                    return False
            return True



    def cost_of_attack_path(self, path):
        '''
        The cost of an attack path is the total number of enemy armies in the path.
        In other words, it is the total number of armies in the subpath starting at the second vertex.

        Args:
            path ([int]): a list of territory_ids which must be a valid attack path

        Returns:
            int: the number of enemy armies in the path
        '''

        cost=0
        for country in path:
            if country == path[0]:
                continue
            cost+=self.armies(country)
        return cost




    def shortest_path(self, source, target):
        '''
        This function uses BFS to find the shortest path between source and target.
        This function does not take into account who owns the territories or how many armies are on the territories,
        and so a shortest path is simply a valid path with the smallest number of territories visited.
        This path is not necessarily unique,
        and when multiple shortest paths exist,
        then this function can return any of those paths.

        Args:
            source (int): a territory_id that is the source location
            target (int): a territory_id that is the target location

        Returns:
            [int]: a valid path between source and target that has minimum length; this path is guaranteed to exist
        '''

        stack=[]
        stack.append(source)
        queue = deque([])
        queue.append(stack)

        board=risk.definitions.territory_names
        board=list(board.keys())

        if source==target:
            return stack

        while queue:
            cur_territory = queue.popleft()

            board_info = [territory for territory in board if territory in self.neighbors(cur_territory[-1])]
            for territory in board_info:
                if territory == target:
                    cur_territory.append(territory)
                    # poss.append(cur_territory)
                    # continue
                    return cur_territory
                copy_stack = copy.deepcopy(cur_territory)
                copy_stack.append(territory)
                queue.append(copy_stack)
                board.remove(territory)

    def _fortify(self, source, target):

        stack = []
        stack.append(source)
        queue = deque([])
        queue.append(stack)

        board = risk.definitions.territory_names
        board = list(board.keys())

        if source == target:
            return stack

        while queue:
            cur_territory = queue.popleft()
            player_id=self.owner(cur_territory[-1])
            neighbor=[]
            adj=self.neighbors(cur_territory[-1])
            neighbor=[country for country in adj if self.owner(country)==player_id]
            board_info = [territory for territory in board if territory in neighbor]
            for territory in board_info:
                if territory == target:
                    cur_territory.append(territory)
                    # poss.append(cur_territory)
                    # continue
                    return cur_territory
                copy_stack = copy.deepcopy(cur_territory)
                copy_stack.append(territory)
                queue.append(copy_stack)
                board.remove(territory)


    def can_fortify(self, source, target):

        if self._fortify(source, target) == None:
            return False
        return True



    def cheapest_attack_path(self, source, target):
        '''
        This function uses Dijkstra's algorithm to calculate a cheapest valid attack path between two territories if such a path exists.
        There may be multiple valid cheapest attack paths (in which case it doesn't matter which this function returns),
        or there may be no valid attack paths (in which case the function returns None).

        Args:
            source (int): territory_id of source node
            target (int): territory_id of target node

        Returns:
            [int]: a list of territory_ids representing the valid attack path; if no path exists, then it returns None instead
        '''

        # key is territory and value is path
        territories={}
        territories[source]=[source]
        pq = PriorityQueue()
        pq.put(source, 0)
        visited=[source]

        while pq:
            cur_ter=pq.get()
            # print("cur_ter=", cur_ter)
            if cur_ter==target:
                return territories[cur_ter]
            self.neighbors(cur_ter)
            territorys=list(set(self.neighbors(cur_ter)) - set(visited))
            print("territorys=", territorys)
            for territory in territorys:
                copy_path=copy.deepcopy(territories[cur_ter])
                copy_path.append(territory)
                # priority=
                # pq.put(territory, priority)
                return

    def _attack(self, source, target):

        stack = []
        stack.append(source)
        queue = deque([])
        queue.append(stack)

        board = risk.definitions.territory_names
        board = list(board.keys())

        if source == target:
            return stack

        while queue:
            cur_territory = queue.popleft()
            player_id = self.owner(source)
            neighbor = []
            adj = self.neighbors(cur_territory[-1])
            neighbor = [country for country in adj if self.owner(country) != player_id]
            board_info = [territory for territory in board if territory in neighbor]
            for territory in board_info:
                if territory == target:
                    cur_territory.append(territory)
                    return cur_territory
                copy_stack = copy.deepcopy(cur_territory)
                copy_stack.append(territory)
                queue.append(copy_stack)
                board.remove(territory)

    def can_attack(self, source, target):
        '''
        Args:
            source (int): territory_id of source node
            target (int): territory_id of target node

        Returns:
            bool: True if a valid attack path exists between source and target; else False
        '''
        print("path=", self.shortest_path(source, target))

        if self._attack(source, target) == None or source==target:
            return False
        return True
        # if self.shortest_path(source, target) == None:
        #     return False
        #
        # paths = self._all_paths(source, target)
        # print("paths=", paths)
        # for path in paths:
        #     print("path1=", path)
        #     if self._can_attack(path, source, target):
        #         return True
        # return False


    # ======================= #
    # == Continent Methods == #
    # ======================= #

    def continent(self, continent_id):
        """
        Create a generator of all territories that belong to a given continent.
            
        Args:
            continent_id (int): ID of the continent.

        Returns:
            generator: Generator of Territories.
        """
        return (t for t in self.data if t.territory_id in risk.definitions.continent_territories[continent_id])

    def n_continents(self, player_id):
        """
        Calculate the total number of continents owned by a player.
        
        Args:
            player_id (int): ID of the player.
                
        Returns:
            int: Number of continents owned by the player.
        """
        return len([continent_id for continent_id in range(6) if self.owns_continent(player_id, continent_id)])

    def owns_continent(self, player_id, continent_id):
        """
        Check if a player owns a continent.
        
        Args:
            player_id (int): ID of the player.
            continent_id (int): ID of the continent.
            
        Returns:
            bool: True if the player owns all of the continent's territories.
        """
        return all((t.player_id == player_id for t in self.continent(continent_id)))

    def continent_owner(self, continent_id):
        """
        Find the owner of all territories in a continent. If the continent
        is owned by various players, return None.
            
        Args:
            continent_id (int): ID of the continent.
                
        Returns:
            int/None: Player_id if a player owns all territories, else None.
        """
        pids = set([t.player_id for t in self.continent(continent_id)])
        if len(pids) == 1:
            return pids.pop()
        return None

    def continent_fraction(self, continent_id, player_id):
        """
        Compute the fraction of a continent a player owns.
        
        Args:
            continent_id (int): ID of the continent.
            player_id (int): ID of the player.

        Returns:
            float: The fraction of the continent owned by the player.
        """
        c_data = list(self.continent(continent_id))
        p_data = [t for t in c_data if t.player_id == player_id]
        return float(len(p_data)) / len(c_data)

    def num_foreign_continent_territories(self, continent_id, player_id):
        """
        Compute the number of territories owned by other players on a given continent.
        
        Args:
            continent_id (int): ID of the continent.
            player_id (int): ID of the player.

        Returns:
            int: The number of territories on the continent owned by other players.
        """
        return sum(1 if t.player_id != player_id else 0 for t in self.continent(continent_id))

    # ==================== #
    # == Action Methods == #
    # ==================== #    

    def reinforcements(self, player_id):
        """
        Calculate the number of reinforcements a player is entitled to.
            
        Args:
            player_id (int): ID of the player.

        Returns:
            int: Number of reinforcement armies that the player is entitled to.
        """
        base_reinforcements = max(3, int(self.n_territories(player_id) / 3))
        bonus_reinforcements = 0
        for continent_id, bonus in risk.definitions.continent_bonuses.items():
            if self.continent_owner(continent_id) == player_id:
                bonus_reinforcements += bonus
        return base_reinforcements + bonus_reinforcements

    def possible_attacks(self, player_id):
        """
        Assemble a list of all possible attacks for the players.

        Args:
            player_id (int): ID of the attacking player.

        Returns:
            list: List of Moves.
        """
        return [Move(from_t.territory_id, from_t.armies, to_t.territory_id, to_t.player_id, to_t.armies)
                for from_t in self.mobile(player_id) for to_t in self.hostile_neighbors(from_t.territory_id)]

    def possible_fortifications(self, player_id):
        """
        Assemble a list of all possible fortifications for the players.
        
        Args:
            player_id (int): ID of the attacking player.

        Returns:
            list: List of Moves.
        """
        return [Move(from_t.territory_id, from_t.armies, to_t.territory_id, to_t.player_id, to_t.armies)
                for from_t in self.mobile(player_id) for to_t in self.friendly_neighbors(from_t.territory_id)]

    def fortify(self, from_territory, to_territory, n_armies):
        """
        Perform a fortification.

        Args:
            from_territory (int): Territory_id of the territory where armies leave.
            to_territory (int): Territory_id of the territory where armies arrive.
            n_armies (int): Number of armies to move.

        Raises:
            ValueError if the player moves too many or negative armies.
            ValueError if the territories do not share a border or are not owned by the same player.
        """
        if n_armies < 0 or self.armies(from_territory) <= n_armies:
            raise ValueError('Board: Cannot move {n} armies from territory {tid}.'
                             .format(n=n_armies, tid=from_territory))
        if to_territory not in [t.territory_id for t in self.friendly_neighbors(from_territory)]:
            raise ValueError('Board: Cannot fortify, territories do not share owner and/or border.')
        self.add_armies(from_territory, -n_armies)
        self.add_armies(to_territory, +n_armies)

    def attack(self, from_territory, to_territory, attackers):
        """
        Perform an attack.

        Args:
            from_territory (int): Territory_id of the offensive territory.
            to_territory (int): Territory_id of the defensive territory.
            attackers (int): Number of attacking armies.

        Raises:
            ValueError if the number of armies is <1 or too large.
            ValueError if a player attacks himself or the territories do not share a border.

        Returns:
            bool: True if the defensive territory was conquered, False otherwise.
        """
        if attackers < 1 or self.armies(from_territory) <= attackers:
            raise ValueError('Board: Cannot attack with {n} armies from territory {tid}.'
                             .format(n=attackers, tid=from_territory))
        if to_territory not in [tid for (tid, _, _) in self.hostile_neighbors(from_territory)]:
            raise ValueError('Board: Cannot attack, territories do not share border or are owned by the same player.')
        defenders = self.armies(to_territory)
        def_wins, att_wins = self.fight(attackers, defenders)
        if self.armies(to_territory) == att_wins:
            self.add_armies(from_territory, -attackers)
            self.set_armies(to_territory, attackers - def_wins)
            self.set_owner(to_territory, self.owner(from_territory))
            return True
        else:
            self.add_armies(from_territory, -def_wins)
            self.add_armies(to_territory, -att_wins)
            return False

    # ====================== #
    # == Plotting Methods == #
    # ====================== #    

    def plot_board(self, path=None, plot_graph=False, filename=None):
        """ 
        Plot the board. 
        
        Args:
            path ([int]): a path of territory_ids to plot
            plot_graph (bool): if true, plots the graph structure overlayed on the board
            filename (str): if given, the plot will be saved to the given filename instead of displayed
        """
        im = plt.imread(os.getcwd() + '/img/risk.png')
        dpi=96
        img_width=800
        fig, ax = plt.subplots(figsize=(img_width/dpi, 300/dpi), dpi=dpi)
        _ = plt.imshow(im)
        plt.axis('off')
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())

        def plot_path(xs):
            if not self.is_valid_path(xs):
                print('WARNING: not a valid path')
            coor = risk.definitions.territory_locations[xs[0]]
            verts=[(coor[0]*1.2, coor[1]*1.22 + 25)]
            codes = [ Path.MOVETO ]
            for i,x in enumerate(xs[1:]):
                if (xs[i]==19 and xs[i+1]==1) or (xs[i]==1 and xs[i+1]==19):
                    coor = risk.definitions.territory_locations[x]
                    #verts.append((coor[0]*1.2, coor[1]*1.22 + 25))
                    verts.append((1000,-200))
                    verts.append((coor[0]*1.2, coor[1]*1.22 + 25))
                    codes.append(Path.CURVE3)
                    codes.append(Path.CURVE3)
                else:
                    coor = risk.definitions.territory_locations[x]
                    verts.append((coor[0]*1.2, coor[1]*1.22 + 25))
                    codes.append(Path.LINETO)
            path = Path(verts, codes)
            patch = patches.PathPatch(path, facecolor='none', lw=2)
            ax.add_patch(patch)

        if path is not None:
            plot_path(path)

        if plot_graph:
            for t in risk.definitions.territory_neighbors:
                path = []
                for n in risk.definitions.territory_neighbors[t]:
                    path.append(t)
                    path.append(n)
                plot_path(path)

        for t in self.data:
            self.plot_single(t.territory_id, t.player_id, t.armies)

        if not filename:
            plt.show()
        else:
            plt.tight_layout()
            plt.savefig(filename,bbox_inches='tight')

    @staticmethod
    def plot_single(territory_id, player_id, armies):
        """
        Plot a single army dot.
            
        Args:
            territory_id (int): the id of the territory to plot,
            player_id (int): the player id of the owner,
            armies (int): the number of armies.
        """
        coor = risk.definitions.territory_locations[territory_id]
        plt.scatter(
            [coor[0]*1.2], 
            [coor[1]*1.22], 
            s=100, 
            c=risk.definitions.player_colors[player_id],
            zorder=2
            )
        plt.text(
            coor[0]*1.2, 
            coor[1]*1.22 + 25, 
            s=str(armies),
            color='black' if risk.definitions.player_colors[player_id] in ['yellow', 'pink'] else 'white',
            ha='center', 
            size=7
            )

    # ==================== #
    # == Combat Methods == #
    # ==================== #    

    @classmethod
    def fight(cls, attackers, defenders):
        """
        Stage a fight.

        Args:
            attackers (int): Number of attackers.
            defenders (int): Number of defenders.

        Returns:
            tuple (int, int): Number of lost attackers, number of lost defenders.
        """
        n_attack_dices = min(attackers, 3)
        n_defend_dices = min(defenders, 2)
        attack_dices = sorted([cls.throw_dice() for _ in range(n_attack_dices)], reverse=True)
        defend_dices = sorted([cls.throw_dice() for _ in range(n_defend_dices)], reverse=True)
        wins = [att_d > def_d for att_d, def_d in zip(attack_dices, defend_dices)]
        return len([w for w in wins if w is False]), len([w for w in wins if w is True])

    @staticmethod
    def throw_dice():
        """
        Throw a dice.
        
        Returns:
            int: random int in [1, 6]. """
        return random.randint(1, 6)

    # ======================= #
    # == Territory Methods == #
    # ======================= #

    def owner(self, territory_id):
        """
        Get the owner of the territory.

        Args:
            territory_id (int): ID of the territory.

        Returns:
            int: Player_id that owns the territory.
        """
        return self.data[territory_id].player_id

    def armies(self, territory_id):
        """
        Get the number of armies on the territory.

        Args:
            territory_id (int): ID of the territory.

        Returns:
            int: Number of armies in the territory.
        """
        return self.data[territory_id].armies

    def set_owner(self, territory_id, player_id):
        """
        Set the owner of the territory.

        Args:
            territory_id (int): ID of the territory.
            player_id (int): ID of the player.
        """
        self.data[territory_id] = Territory(territory_id, player_id, self.armies(territory_id))

    def set_armies(self, territory_id, n):
        """
        Set the number of armies on the territory.

        Args:
            territory_id (int): ID of the territory.
            n (int): Number of armies on the territory.

        Raises:
            ValueError if n < 1.
        """
        if n < 1:
            raise ValueError('Board: cannot set the number of armies to <1 ({tid}, {n}).'.format(tid=territory_id, n=n))
        self.data[territory_id] = Territory(territory_id, self.owner(territory_id), n)

    def add_armies(self, territory_id, n):
        """
        Add (or remove) armies to/from the territory.

        Args:
            territory_id (int): ID of the territory.
            n (int): Number of armies to add to the territory.

        Raises:
            ValueError if the resulting number of armies is <1.
        """
        self.set_armies(territory_id, self.armies(territory_id) + n)

    def n_armies(self, player_id):
        """
        Count the total number of armies owned by a player.

        Args:
            player_id (int): ID of the player.

        Returns:
            int: Number of armies owned by the player.
        """
        return sum((t.armies for t in self.data if t.player_id == player_id))

    def n_territories(self, player_id):
        """
        Count the total number of territories owned by a player.

        Args:
            player_id (int): ID of the player.

        Returns:
            int: Number of territories owned by the player.
        """
        return len([None for t in self.data if t.player_id == player_id])

    def territories_of(self, player_id):
        """
        Return a set of all territories owned by the player.

        Args:
            player_id (int): ID of the player.

        Returns:
            list: List of all territory IDs owner by the player.
        """
        return [t.territory_id for t in self.data if t.player_id == player_id]

    def mobile(self, player_id):
        """
        Create a generator of all territories of a player which can attack or move,
        i.e. that have more than one army.

        Args:
            player_id (int): ID of the attacking player.

        Returns:
            generator: Generator of Territories.
        """
        return (t for t in self.data if (t.player_id == player_id and t.armies > 1))


from risk.board import Board,Territory
import copy

# define boards for the tests
# HINT: I recommend you plot these boards
board0 = Board([Territory(territory_id=i, player_id=1, armies=i%5+1) for i in range(42)])

board1 = copy.deepcopy(board0)
board1.set_owner(3,0)
board1.set_armies(3,500)
board1.set_armies(4,500)
board1.set_armies(34,500)
board1.set_armies(39,500)
board1.set_armies(35,500)

board2 = copy.deepcopy(board1)
board2.set_owner(34, 0)
board2.set_armies(34,1)
board2.set_owner(35, 0)
board2.set_armies(35,1)
board2.set_owner(39, 0)
board2.set_armies(39,1)

board3 = copy.deepcopy(board2)
board3.set_owner(34, 1)

board4 = copy.deepcopy(board2)
board4.set_owner(4, 0)
board4.set_armies(4, 1)
board4.set_owner(1, 0)

board5 = Board([Territory(territory_id=i, player_id=i%5, armies=i%5+1) for i in range(42)])




assert board1.can_attack(3,24)
assert board2.can_attack(3,24)
assert board3.can_attack(3,24)
assert not board4.can_attack(3,24)
assert board5.can_attack(3,24)
assert board5.can_attack(30,24)
assert board5.can_attack(3,6)
assert not board5.can_attack(3,18)
assert board5.can_attack(38,1)
assert board5.can_attack(3,2)
assert not board5.can_attack(3,3)


# print(board1.cheapest_attack_path(3,24))
# assert board1.cost_of_attack_path(board1.cheapest_attack_path(3,24)) == 34
# assert board2.cost_of_attack_path(board2.cheapest_attack_path(3,24)) == 34
# assert board3.cost_of_attack_path(board3.cheapest_attack_path(3,24)) == 31
# assert board4.cheapest_attack_path(3,24) is None
# assert board5.cost_of_attack_path(board5.cheapest_attack_path(3,24)) == 10
# assert board5.cost_of_attack_path(board5.cheapest_attack_path(30,24)) == 13
# assert board5.cost_of_attack_path(board5.cheapest_attack_path(3,6)) == 17
# assert board5.cheapest_attack_path(3,18) is None
# assert board5.cost_of_attack_path(board5.cheapest_attack_path(38,1)) == 16
# assert board5.cost_of_attack_path(board5.cheapest_attack_path(3,2)) == 13
# assert board5.cheapest_attack_path(3,3) is None