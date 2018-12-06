# mdpAgents.py
# parsons/20-nov-2017
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

# The agent here is was written by Henry George, based on the code in
# pacmanAgents.py

import random
import time
import api
import math
import util
from game import Agent
from pacman import Directions


# Preset Map Values
class MapValues:
    GhostValue = -30
    EdibleGhostValue = 5
    NullValue = 0
    FoodValue = 10
    NullPunishmentValue = -1


# MDP variables
class MDPValues:
    Gamma = 0.99
    Threshold = 0.01
    DirectionNoise = 0.8


class MDPAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up MDPAgent!"
        name = "Pacman"
        self.map = Map()

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print "Running registerInitialState for MDPAgent!"
        corners = api.corners(state)
        (width, height) = sorted(corners, key=lambda x: util.manhattanDistance((0, 0), x), reverse=True)[0]
        self.map.initialise(height, width, api.walls(state))
        self.map.initialiseRewards(api.food(state))

    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"

    # For now I just move randomly
    def getAction(self, state):
        ghosts = api.ghosts(state)
        self.map.updatePunishments(ghosts)
        location = api.whereAmI(state)
        self.map.updateRewards(location)
        self.map.updateUtilities()
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)
        return api.makeMove(self.map.optimalMove(location, legal), legal)


### Helper Functions and Architecture ###

# An object to represent each node in the graph generated
class Node():
    # A list of all neighboring nodes


    def __init__(self, position, reward=MapValues.NullValue, punishment=MapValues.NullPunishmentValue):
        self.position = position
        self.reward = reward  # Food can be updated simply, with a 'did I eat this move?'.
        self.punishment = punishment  # Ghost position and effect changes dramatically so needs to be completely rebuilt
        self.utility = reward + punishment
        self.connected = []
        self.directionallyConnected = []
        self.directionProbabilities = {}


    # The minimum distance from one point to another |x_1 - x_2| + |y_1 - y_2|
    def minimumDistance(self, other):
        return util.manhattanDistance(self.whichNode(), other.whichNode())

    def getValue(self):
        return self.reward + self.punishment

    def whichNode(self):
        return self.position

    def setReward(self, value):
        self.reward = value

    def setPunishment(self, value):
        self.punishment = value

    def updatePunishment(self, value):
        self.punishment += value

    def rewardFunction(self):
        return self.reward + self.punishment

    def printNode(self):
        character = "?"
        if self.reward == MapValues.EdibleGhostValue:
            character = "O"
        elif self.reward == MapValues.FoodValue:
            character = "."
        elif self.punishment == MapValues.GhostValue:
            character = "X"
        print character,

    def printNodeUtility(self):
        print str(round(self.utility)) + '(' + str(int(self.reward)) +  ',' + str(int(self.punishment)) + ')\t',

    def legalDirections(self):
        if not len(self.directionallyConnected):
            for node in self.connected:
                self.directionallyConnected.append(
                    DirectionalLocation(position=self.position, nextPosition=node.position)
                )
        return self.directionallyConnected

    def probabilities(self, direction):
        if not self.directionProbabilities:
            self.initialiseDirectionProbabilities()
        return self.directionProbabilities[direction.nextPosition]

    def initialiseDirectionProbabilities(self):
        legal = self.legalDirections()
        for attemptedAction in legal:
            self.directionProbabilities[attemptedAction.nextPosition] = {}
            self.directionProbabilities[attemptedAction.nextPosition][attemptedAction.nextPosition] = MDPValues.DirectionNoise
            adjacent = attemptedAction.adjacentTo()
            self.directionProbabilities[attemptedAction.nextPosition][self.position] = 0
            for probableMove in adjacent:
                probableDirectionLocation = DirectionalLocation(direction=probableMove, position=self.position)
                if probableMove in [move.direction for move in legal]:
                    self.directionProbabilities[attemptedAction.nextPosition][probableDirectionLocation.nextPosition] = ( 1 - MDPValues.DirectionNoise ) / len(adjacent)
                else:
                    self.directionProbabilities[attemptedAction.nextPosition][self.position] += ( 1 - MDPValues.DirectionNoise ) / len(adjacent)


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
            # This can be optimised
            self._map[key].connected = [node for node in self._map.values() if
                                        node.minimumDistance(self._map[key]) == 1]

    def display(self):
        for y in range(0, self.getHeight())[::-1]:
            for x in range(0, self.getWidth()):
                if self._map.get((x, y), None):
                    self._map.get((x, y)).printNode()
                else:
                    print u"\u2610",
            print


    def displayUtilities(self):
        for y in range(0, self.getHeight())[::-1]:
            for x in range(0, self.getWidth()):
                if self._map.get((x, y), None):
                    self._map.get((x, y)).printNodeUtility()
                else:
                    print u"\u2610\t",
            print

    # Here x and y are indices.
    def setReward(self, position, value):
        self._map[(position[0], position[1])].setReward(value)

    def getValue(self, position):
        return self._map[(position[0], position[1])].getValue()

    # Return width and height
    def getHeight(self):
        return self._height + 1

    def getWidth(self):
        return self._width + 1

    def updateUtilities(self):
        terminalIteration = False
        while not terminalIteration:
            threshholdHolds = True
            # Each iteration of Value Iteration
            for position in self._map.keys():
                node = self._map.get(position)
                actionUtilities = []
                for action in node.legalDirections():
                    states = []
                    for state in node.probabilities(action).keys():
                        states.append(node.probabilities(action)[state] * self._map.get(state).utility)
                    actionUtility = sum(states)
                    actionUtilities.append(actionUtility)
                utility = node.rewardFunction() + MDPValues.Gamma * max(actionUtilities)
                if abs(utility - node.utility) > MDPValues.Threshold:
                    threshholdHolds = False
                node.utility = utility
            terminalIteration = threshholdHolds


    def initialiseRewards(self, food):
        for piece in food:
            self.setReward(piece, MapValues.FoodValue)


    def updateRewards(self, position):
        self.setReward(position, MapValues.NullValue)


    def updatePunishments(self, ghosts):
        seen = []
        for ghost in ghosts:
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


    def optimalMove(self, position, legal):
        moves = []
        node = self._map.get(position)
        for move in legal:
            moves.append((move, self._map.get(DirectionalLocation(position=position, direction=move).nextPosition).utility))
        optimalMoves = sorted(moves, key=lambda x: x[1], reverse=True)
        return optimalMoves[0][0]

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
            raise NotImplementedError("Unsupported Direction: " + str(self._direction))





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


