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

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util


# Utility factors that influence action choice
UTILITY = {
    'unseen': 1, # Value of travelling to unseen spots
    'ghost' : -5, # Value of travelling towards a ghost
    'capsule': 1, # Value of a capsule
}


class PartialAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up!"
        name = "Pacman"
        self.map = {}

    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like I just died!"
        self.map = None

    # For now I just move randomly
    def getAction(self, state):
        # Get the actions we can try, and remove "STOP" if that is one of them.
        if not self.map:
            self.map = fill_map(state)
        location = api.whereAmI(state)
        self.map[location].seen = True
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)
        # Random choice between the legal options.
        utility = [(calculate_utility(direction, self.map, state), direction) for direction in legal]
        utility.sort(key=lambda x: x[0], reverse=True)
        return api.makeMove(utility[0][1], legal)


def fill_map(state):
    # Creates a graph of the traversible points on the map (as an adjacency set within a set)

    unvisited = {}
    corners = api.corners(state)
    walls = api.walls(state)

    # Add all nodes that aren't walls ( Assume all pacman layouts are rectangular and start at (0,0) )
    dimensions = sorted(corners, key=lambda x: util.manhattanDistance((0,0), x), reverse=True)[0]
    for x in range(0, dimensions[0] + 1):
        for y in range(0, dimensions[1] + 1):
            if (x, y) not in walls:
                unvisited[(x,y)] = Node((x, y))

    # Add neighbors
    keys = unvisited.iterkeys()
    for key in keys:
        unvisited[key].connected = [node for node in unvisited.values() if node.distance(unvisited[key]) == 1]
    # Return map
    return unvisited


class Node():

    connected = []

    def __init__(self, value):
        self.value = value
        self.seen = False

    def distance(self, other):
        return util.manhattanDistance(self.value, other.value)

    def distance_to_unseen(self):
        # Simple BFS to find distance to nearest unseen food
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


def calculate_utility(direction, map, state):
    next_location = nextLocation(direction, api.whereAmI(state))
    unseen_value = - map[next_location].distance_to_unseen()
    utility = UTILITY['unseen'] * unseen_value + UTILITY['ghost'] * ghost_value(direction, state)
    return utility


def ghost_value(direction, state):
    ghosts = api.ghosts(state)
    location = api.whereAmI(state)
    danger = 0
    for ghost in ghosts:
        danger += directional_weight(location, ghost)[direction] / util.manhattanDistance(location, ghost)
    return danger




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

    return {
        Directions.NORTH: north,
        Directions.SOUTH: south,
        Directions.EAST: east,
        Directions.WEST: west
    }