# mdpAgents.py
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Henry George on Dec 6 2018, based on the code in
# pacmanAgents.py

import math

import api
import util
from game import Agent
from pacman import Directions

# When True will print utilities of each move and display map after initialisation
DEBUG = False

# It was unsure whether pacman should be allowed to stop if this is ever the optimal move. This happens very
# little in practice, but the option to toggle is here in case
CAN_STOP = False

# Preset Map Values
class MapValues:
    GhostValue = -5 # Amount of danger for a ghost
    EdibleGhostValue = 5 # This was not implemented
    NullValue = 0 # This is the Null value for positive/negative reward - DO NOT CHANGE
    FoodValue = 1 # Reward gained from eating food
    NullPunishmentValue = -0.1 # Punishment for any given empty square


# MDP variables
class MDPValues:
    Gamma = 0.65 # This gamma was found to balance long and short term goals
    Threshold = 0.1 # This is not a percentage, it is a raw difference to compare with delta U_i
    DirectionNoise = 0.8 # A percentage - fixed by the api.py - DO NOT CHANGE


# MDP Agent which calculates optimal utility using Bellman's Formula for Value Iteration
class MDPAgent(Agent):

    def __init__(self):
        print "Starting up MDPAgent!"
        name = "Uncoordinated Pacman"
        self.map = Map()

    # Initialise Map
    def registerInitialState(self, state):
        print "Initialising Map..."
        corners = api.corners(state)
        # The furthest corner from (0, 0) gives the width and height of the map (given it starts at (0, 0))
        (width, height) = sorted(corners, key=lambda x: util.manhattanDistance((0, 0), x), reverse=True)[0]
        self.map.initialise(height, width, api.walls(state))
        # Set base values for rewards (set food but not ghosts)
        self.map.initialiseRewards(api.food(state))
        # Print map when debugging
        if DEBUG:
            self.map.display()

    # This is what gets run in between multiple games
    def final(self, state):
        print "Game Over."

    # Update the rewards (positive aspects of reward function) and Punishments (negative aspects of reward function)
    # Then run Value Iteration (updateUtilities) to calculate the optimalMove.
    def getAction(self, state):
        ghosts = api.ghosts(state)
        self.map.updatePunishments(ghosts)
        location = api.whereAmI(state)
        self.map.updateRewards(location)
        self.map.updateUtilities()
        legal = api.legalActions(state)

        if CAN_STOP:
            if Directions.STOP in legal:
                legal.remove(Directions.STOP)
        return api.makeMove(self.map.optimalMove(location, legal), legal)



# An object to represent each node in the graph generated
class Node():

    # Food is the only positive reward (feared ghosts were not implemented), and has an almost identical reward function
    # from one turn to the next, whereas ghosts change dramatically, and so have been separated into two layers.
    # The positive 'reward' layer, and the negative 'punishment' layer. Both of these are taken into account when
    # calculating the utility - see rewardFunction, but are updated separately to optimise performance.

    def __init__(self, position, reward=MapValues.NullValue, punishment=MapValues.NullPunishmentValue):
        self.position = position
        self.reward = reward  # Food can be updated simply, with a 'did I eat this move?'
        self.punishment = punishment  # Ghost position and effect changes dramatically so needs to be completely rebuilt
        self.utility = reward + punishment # Base utility of each node. After the initial round last rounds utilities are used instead
        self.connected = [] # A list of neighboring nodes
        self.directionallyConnected = [] # A list of neighboring directionalLocations
        self.directionProbabilities = {} # A dictionary of dictionaries, each describing the probability distribution P(s'|s, a)

    # The minimum distance from one point to another |x_1 - x_2| + |y_1 - y_2|
    def minimumDistance(self, other):
        return util.manhattanDistance(self.position, other.position)

    # Setter for positive reward
    def setReward(self, value):
        self.reward = value

    # Getter for negative reward (punishment)
    def setPunishment(self, value):
        self.punishment = value

    # For updating punishment values that were already changed in this round
    def updatePunishment(self, value):
        self.punishment += value

    # The reward function, taking into account positive and negative reward - used directly in Bellman's
    def rewardFunction(self):
        return self.reward + self.punishment

    # A print helper function - IGNORE
    def printNode(self):
        character = "?"
        if self.reward == MapValues.EdibleGhostValue:
            character = "O"
        elif self.reward == MapValues.FoodValue:
            character = "."
        elif self.punishment == MapValues.GhostValue:
            character = "X"
        print character,

    # A debug print helper function - IGNORE
    def printNodeUtility(self):
        print str(round(self.utility)) + '(' + str(int(self.reward)) + ',' + str(int(self.punishment)) + ')\t',

    # Lazy initialises the set of legalDirections - returns a set of DirectionalLocations from node to neighbors
    # This is constant accross rounds
    def legalDirections(self):
        if not len(self.directionallyConnected):
            for node in self.connected:
                self.directionallyConnected.append(
                    DirectionalLocation(position=self.position, nextPosition=node.position)
                )
        return self.directionallyConnected

    # Lazy initialises the probability distribution of P(s'|s, a) - This is constant between rounds
    def probabilities(self, direction):
        if not self.directionProbabilities:
            self.initialiseDirectionProbabilities()
        return self.directionProbabilities[direction.nextPosition]

    # Builds a dictionary of dicts to represent P(s'|s, a)
    def initialiseDirectionProbabilities(self):
        legal = self.legalDirections()
        # For each legal move, we build a distribution across the possible outcomes
        for attemptedAction in legal:
            self.directionProbabilities[attemptedAction.nextPosition] = {} # For each action we build a dict
            self.directionProbabilities[attemptedAction.nextPosition][
                attemptedAction.nextPosition] = MDPValues.DirectionNoise # The move we are attempting to make has P = 0.8
            adjacent = attemptedAction.adjacentTo()
            self.directionProbabilities[attemptedAction.nextPosition][self.position] = 0
            # For each move adjacent to the move we are attempting to make, if the adjacent move is not legal, the
            # probability is added to Directions.STOP, but if legal, is added to that direction instead.
            # This is how I have understood the specification.
            for probableMove in adjacent:
                probableDirectionLocation = DirectionalLocation(direction=probableMove, position=self.position)
                if probableMove in [move.direction for move in legal]:
                    self.directionProbabilities[attemptedAction.nextPosition][
                        probableDirectionLocation.nextPosition] = (1 - MDPValues.DirectionNoise) / len(adjacent)
                else:
                    # The (1 - 0.8) / len(adj) ensures that the distribution we create is a probability distribution
                    # since in total we have 0.8 + len(adj) * (1 - 0.8) / len(adj) = 1
                    self.directionProbabilities[attemptedAction.nextPosition][self.position] += (1 - MDPValues.DirectionNoise) / len(adjacent)


# A map made up of Nodes (see above) the nodes are stored in a dictionary indexed by position (x, y), only valid moves
# are stored in the map, walls are not.
class Map():

    def __init__(self):
        self._map = dict()
        self._height = 0
        self._width = 0

    # Sets the base state of the map
    def initialise(self, height, width, walls):
        self._height = height
        self._width = width
        for x in range(0, width + 1):
            for y in range(0, height + 1):
                if (x, y) not in walls:
                    self._map[(x, y)] = Node((x, y))
        keys = self._map.iterkeys()
        for key in keys:
            # TODO: This can be optimised by only considering the 4 possible neighbors, rather than all map.values()
            self._map[key].connected = [node for node in self._map.values() if
                                        node.minimumDistance(self._map[key]) == 1]

    # Displays the map (not very beautifully)
    def display(self):
        for y in range(0, self.getHeight())[::-1]:
            for x in range(0, self.getWidth()):
                if self._map.get((x, y), None):
                    self._map.get((x, y)).printNode()
                else:
                    print u"\u2610",
            print

    # Displays the map with utilties, and reward / punishment. - also not beautiful
    def displayUtilities(self):
        for y in range(0, self.getHeight())[::-1]:
            for x in range(0, self.getWidth()):
                if self._map.get((x, y), None):
                    self._map.get((x, y)).printNodeUtility()
                else:
                    print u"\u2610\t",
            print


    # Sets the reward of a given node
    def setReward(self, position, value):
        self._map[(position[0], position[1])].setReward(value)

    # Return width and height
    def getHeight(self):
        return self._height + 1


    def getWidth(self):
        return self._width + 1

    # Where the magic happens.
    # This is a Value Iteration using the Bellman Equation.
    # The ValueIteration continues until the change in each value is less than the threshold.
    def updateUtilities(self):
        terminalIteration = False
        while not terminalIteration:
            threshholdHolds = True

            # Each iteration of Value Iteration
            # U_i+1 <- R(s) + gamma * max a in A(s)}( sum{s' caused by a} P(s'|s,a) * U_i(s')
            for position in self._map.keys():
                node = self._map.get(position)
                actionUtilities = []
                # For a in A(s)
                for action in node.legalDirections():
                    states = []
                    # Summing over s' for a given a
                    for state in node.probabilities(action).keys():
                        states.append(node.probabilities(action)[state] * self._map.get(state).utility)
                    actionUtility = sum(states)
                    actionUtilities.append(actionUtility)
                # Main equation to calculate U_i+1
                utility = node.rewardFunction() + MDPValues.Gamma * max(actionUtilities)

                # If any of the utilities have changed by more than the Threshold we do another iteration
                if abs(utility - node.utility) > MDPValues.Threshold:
                    threshholdHolds = False
                node.utility = utility

            terminalIteration = threshholdHolds


    # Adds food rewards to map
    def initialiseRewards(self, food):
        for piece in food:
            self.setReward(piece, MapValues.FoodValue)

    # Since only one piece of food can be eaten at once, this is highly performant
    def updateRewards(self, position):
        self.setReward(position, MapValues.NullValue)

    # Updates the punishments based on ghost position
    # 1. Ghosts can be in float positions - but only across one axis, so we generate up to 2 positions from any ghost
    # 2. The square in which the ghost is in is affected the most, but neighboring squares are also punished to a lesser degree
    # 3. Squares which are 3 away from the ghost are re-initialised, so that any effect from the previous round is removed,
    # without having to reinitialise all nodes
    # To stop overlapping punishments from eliminating each other we keep track of seen squares and update instead of replace.
    def updatePunishments(self, ghosts):
        seen = []
        for ghost in ghosts:
            # 1. Generate Ghost Squares
            positions = floatPositionToIntegers(ghost)
            for position in positions:
                start = self._map.get(position)
                if start not in seen:
                    start.setPunishment(MapValues.GhostValue)
                    seen.append(start)
                else:
                    start.updatePunishment(MapValues.GhostValue)
                neighbors = start.connected
                for node in neighbors:
                    amount = MapValues.GhostValue / len(neighbors)
                    if node not in seen:
                        node.setPunishment(amount)
                        seen.append(node)
                    else:
                        node.updatePunishment(amount)
                    for secondNeighbor in node.connected:
                        if secondNeighbor not in seen:
                            secondNeighbor.setPunishment(MapValues.NullPunishmentValue)

    # Calculates the optimal move out of the legal actions - needs to be run after updateUtilities.
    def optimalMove(self, position, legal):
        moves = []
        node = self._map.get(position)
        for move in legal:
            moves.append(
                (move, self._map.get(DirectionalLocation(position=position, direction=move).nextPosition).utility))
        optimalMoves = sorted(moves, key=lambda x: x[1], reverse=True)
        # Debugging information - IGNORE
        if DEBUG:
            print(optimalMoves)
        # Select the direction component of the first (highest utility) move
        return optimalMoves[0][0]


# A class to assist with converting between locations and directions.
# Given any two of position, nextPosition and direction, can generate the third.
class DirectionalLocation():
    """At least two of the three initial parameters should be given"""

    def __init__(self, position=None, direction=None, nextPosition=None):
        self._position = position
        self._direction = direction
        self._nextPosition = nextPosition

    @property
    def nextPosition(self):
        if self._nextPosition is not None:
            return self._nextPosition
        else:
            if self._direction == Directions.EAST:
                self._nextPosition = (self._position[0] + 1, self._position[1])
            elif self._direction == Directions.WEST:
                self._nextPosition = (self._position[0] - 1, self._position[1])
            elif self._direction == Directions.NORTH:
                self._nextPosition = (self._position[0], self._position[1] + 1)
            elif self._direction == Directions.SOUTH:
                self._nextPosition = (self._position[0], self._position[1] - 1)
            elif self._direction == Directions.STOP:
                self._nextPosition = self._position
            else:
                raise NotImplementedError("Unsupported Directional Location")
            return self._nextPosition

    @property
    def direction(self):
        if self._direction is not None:
            return self._direction
        else:
            if util.manhattanDistance(self._position, self._nextPosition) != 1:
                self._direction = Directions.STOP
            elif self._nextPosition[0] - self._position[0] == 1:
                self._direction = Directions.EAST
            elif self._nextPosition[0] - self._position[0] == -1:
                self._direction = Directions.WEST
            elif self._nextPosition[1] - self._position[1] == 1:
                self._direction = Directions.NORTH
            elif self._nextPosition[1] - self._position[1] == -1:
                self._direction = Directions.SOUTH
            else:
                raise NotImplementedError("Unsupported Directional Location")
            return self._direction

    @property
    def position(self):
        if self._position is not None:
            return self._position
        else:
            if self._direction == Directions.EAST:
                self._position = (self._nextPosition[0] - 1, self._nextPosition[1])
            elif self._direction == Directions.WEST:
                self._position = (self._nextPosition[0] + 1, self._nextPosition[1])
            elif self._direction == Directions.NORTH:
                self._position = (self._nextPosition[0], self._nextPosition[1] - 1)
            elif self._direction == Directions.SOUTH:
                self._position = (self._nextPosition[0], self._nextPosition[1] + 1)
            elif self._direction == Directions.STOP:
                self._position = self._nextPosition
            else:
                raise NotImplementedError("Unsupported Directional Location")
            return self._position

    # Given a direction, return the directions that are adjacent
    def adjacentTo(self):

        if self.direction == Directions.EAST or self.direction == Directions.WEST:
            return [
                Directions.NORTH,
                Directions.SOUTH
            ]
        elif self.direction == Directions.NORTH or self.direction == Directions.SOUTH:
            return [
                Directions.WEST,
                Directions.EAST
            ]
        elif self.direction == Directions.STOP:
            return [
                Directions.NORTH,
                Directions.SOUTH,
                Directions.EAST,
                Directions.WEST
            ]
        else:
            raise NotImplementedError("Unsupported Direction")


# Helper function to turn a position with only one float into two int-based positions on either side of it.
# Eg (1, 1.5) -> [(1, 1), (1, 2)}
def floatPositionToIntegers(position):
    if position[0] < math.ceil(position[0]):
        return [
            (math.ceil(position[0]), position[1]),
            (math.floor(position[0]), position[1])
        ]
    elif position[1] < math.ceil(position[1]):
        return [
            (position[0], math.ceil(position[1])),
            (position[0], math.floor(position[1]))
        ]
    else:
        return [position]


# END