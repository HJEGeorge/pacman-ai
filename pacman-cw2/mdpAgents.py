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

import api
import util
from game import Agent
from pacman import Directions


# Preset Map Values
class MapValues:
    GhostValue = -10
    EdibleGhostValue = 5
    NullValue = 0
    FoodValue = 1


# MDP variables
class MDPValues:
    gamma = 0.75
    threshold = 0.01
    directionProb = 0.8


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
        print "I'm at:"
        print api.whereAmI(state)
        corners = api.corners(state)
        (width, height) = sorted(corners, key=lambda x: util.manhattanDistance((0, 0), x), reverse=True)[0]
        self.map.initialise(height, width, api.walls(state))
        self.map.display()

    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"

    # For now I just move randomly
    def getAction(self, state):
        # Get the actions we can try, and remove "STOP" if that is one of them.
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)
        # Random choice between the legal options.
        return api.makeMove(random.choice(legal), legal)


### Helper Functions and Architecture ###

# Return the co-ordinates of the location caused by travelling in a certain direction (does not check for legality).
def nextLocation(direction, location):
    if direction == Directions.EAST:
        return (location[0] + 1, location[1])
    elif direction == Directions.WEST:
        return (location[0] - 1, location[1])
    elif direction == Directions.NORTH:
        return (location[0], location[1] + 1)
    elif direction == Directions.SOUTH:
        return (location[0], location[1] - 1)
    elif direction == Directions.STOP:
        return location
    else:
        raise NotImplementedError


# An object to represent each node in the graph generated
class Node():
    # A list of all neighboring nodes
    connected = []

    def __init__(self, position, reward=MapValues.NullValue, punishment=MapValues.NullValue):
        self.position = position
        self.reward = reward  # Food can be updated simply, with a 'did I eat this move?'.
        self.punishment = punishment  # Ghost position and effect changes dramatically so needs to be completely rebuilt

    # The minimum distance from one point to another |x_1 - x_2| + |y_1 - y_2|
    def minimumDistance(self, other):
        return util.manhattanDistance(self.whichNode(), other.whichNode())

    def getValue(self):
        return self.reward

    def whichNode(self):
        return self.position

    def setValue(self, value):
        self.reward = value

    def printNode(self):
        character = "?"
        if self.reward == MapValues.EdibleGhostValue:
            character = "O"
        elif self.reward == MapValues.FoodValue:
            character = "."
        elif self.punishment == MapValues.GhostValue:
            character = "X"
        print character,


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
        for x in range(0, self.getWidth()):
            for y in range(0, self.getHeight()):
                if self._map.get((x, y), None):
                    self._map.get((x, y)).printNode()
                else:
                    print u"\u2610",
            print

    # Here x and y are indices.
    def setValue(self, x, y, value):
        self._map[(x, y)].setValue(value)

    def getValue(self, x, y):
        return self._map[(x, y)].getValue()

    # Return width and height
    def getHeight(self):
        return self._height + 1

    def getWidth(self):
        return self._width + 1


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
                raise NotImplementedError
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
                raise NotImplementedError
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
                raise NotImplementedError
            return self._position
