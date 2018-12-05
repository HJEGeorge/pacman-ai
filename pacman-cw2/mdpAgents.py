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

from pacman import Directions
from game import Agent
import api
import random
import game
import util

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

class PartialAgent(Agent):

    # Initialises agent
    def __init__(self):
        print "Initialising!"
        name = "Utilitarian Pacman"
        # A map of all traversable points, and their status (seen/unseen)
        self.map = dict()

    # Runs between games
    def final(self, state):
        print "Game Over"
        # De-initialise map for multiple runs
        self.map = None

    # A utility maximising function, which attempts to choose the most beneficial action based on the environment context
    def getAction(self, state):

        # Builds a map of traversable points for each map given its dimension
        if not self.map:
            self.map = fill_map(state)

        location = api.whereAmI(state)
        # Sets the current location as visited, so that unvisited points are up to date
        self.map[location].seen = True

        # It is never beneficial to stop in this version of the game
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        # Calculates the utility of each action (direction in legal), and selects the action which maximises this utility
        utility = [(calculate_utility(direction, self.map, state), direction) for direction in legal]
        utility.sort(key=lambda x: x[0], reverse=True)
        return api.makeMove(utility[0][1], legal)

### Utility Functions (Business Logic) ###


# Calculate Utility of direction by combining utility of various variables given their associated weights
def calculate_utility(direction, map, state):
    next_location = nextLocation(direction, api.whereAmI(state))
    # Since a longer path is worse, we negate it
    unseen_value = - map[next_location].distance_to_unseen()
    utility = UTILITY['unseen'] * unseen_value \
              + UTILITY['ghost'] * ghost_value(direction, state)
    return utility


# Calculate the danger of ghosts in a specific direction, returns a value between 0-1
# If the ghost is 2 north and 2 east, then each of north and east are 1/2 danger, if ghost is 3 north and 1 east, north is 3/4 danger, and east is 1/4 danger.
def ghost_value(direction, state):
    ghosts = api.ghosts(state)
    location = api.whereAmI(state)
    danger = 0
    for ghost in ghosts:
        distance = util.manhattanDistance(location, ghost)
        if distance:
            danger += directional_weight(location, ghost)[direction] / distance
        else:
            danger += float('inf')
    return danger

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


# Calculate the positive distance in each of North, South, East, West from base to point
def directional_weight(base, point):
    north, south, east, west = 0, 0, 0, 0

    # X-axis calculation
    x = base[0] - point[0]
    if x > 0:
        west = x
    else:
        east = -x

    # Y-axis calculation
    y = base[1] - point[1]
    if y > 0:
        south = y
    else:
        north = -y

    # Return a dictionary of distances in each direction
    return {
        Directions.NORTH: north,
        Directions.SOUTH: south,
        Directions.EAST: east,
        Directions.WEST: west
    }

# An object to represent each node in the graph generated
class Node():
    # A list of all neighboring nodes
    connected = []

    def __init__(self, position, value=MapValues.NullValue):
        self.position = position
        self.value = value

    # The minimum distance from one point to another |x_1 - x_2| + |y_1 - y_2|
    def minimumDistance(self, other):
        return util.manhattanDistance(self.whichNode(), other.whichNode())

    def getValue(self):
        return self.value

    def whichNode(self):
        return self.position

    def setValue(self, value):
        self.value = value

    def printNode(self):
        character = "?"
        if self.value == MapValues.EdibleGhostValue:
            character = "O"
        elif self.value == MapValues.FoodValue:
            character = "."
        elif self.value == MapValues.GhostValue:
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
            self._map[key].connected = [node for node in self._map.values() if node.minimumDistance(self._map[key]) == 1]

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
        return self._map[(x , y)].getValue()

    # Return width and height
    def getHeight(self):
        return self._height + 1

    def getWidth(self):
        return self._width + 1

