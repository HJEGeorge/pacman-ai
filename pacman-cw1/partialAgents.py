# partialAgent.py
# parsons/15-oct-2017
#
# Version 1
#
# The starting point for CW1.
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

# The Agent here was written by Henry George, based on skeleton work from Simon Parsons.
# Written 22/10/18 for 6CCS3AIN - Artificial Intelligence
# Coursework 1 due 28th of October 2018 at King's College London

import api
import util
from game import Agent
from pacman import Directions

# Utility factors that influence action choice

UTILITY = {
    'unseen': 1,  # Value of travelling to unseen spots
    'ghost': -5,  # Value of travelling towards a ghost
    'capsule': 1,  # Value of a capsule (NotImplemented)
}


# A utility maximising agent for all maps, which visits all traversable points on the map while avoiding ghosts
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


# Creates a graph of the traversible points on the map (as an adjacency set within a set)
def fill_map(state):
    unvisited = {}
    corners = api.corners(state)
    walls = api.walls(state)

    # Add all nodes that aren't walls ( Assume all pacman layouts are rectangular and start at (0,0) )
    dimensions = sorted(corners, key=lambda x: util.manhattanDistance((0, 0), x), reverse=True)[0]
    for x in range(0, dimensions[0] + 1):
        for y in range(0, dimensions[1] + 1):
            if (x, y) not in walls:
                unvisited[(x, y)] = Node((x, y))

    # Add neighbors to each node
    keys = unvisited.iterkeys()
    for key in keys:
        unvisited[key].connected = [node for node in unvisited.values() if node.distance(unvisited[key]) == 1]

    # Return map
    return unvisited


# An object to represent each node in the graph generated
class Node():
    # A list of all neighboring nodes
    connected = []

    def __init__(self, value):
        self.value = value
        self.seen = False

    # The minimum distance from one point to another |x_1 - x_2| + |y_1 - y_2|
    def distance(self, other):
        return util.manhattanDistance(self.value, other.value)

    # Simple BFS to find distance to nearest unseen food
    # Returns 0 if this point is unvisited, 1 if one of it's neighbors is unvisited, etc...
    def distance_to_unseen(self):
        if self.seen == False:
            return 0
        queue = [(self, [self])]
        while queue:
            (vertex, path) = queue.pop(0)
            for next in set(vertex.connected) - set(path):
                if not next.seen:
                    return len(path)
                else:
                    queue.append((next, path + [next]))
        raise NotImplementedError('No unvisited points remain but game not complete.')

