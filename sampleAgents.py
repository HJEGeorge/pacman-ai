# sampleAgents.py
# parsons/07-oct-2017
#
# Version 1.1
#
# Some simple agents to work with the PacMan AI projects from:
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

# The agents here are extensions written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util

# RandomAgent
#
# A very simple agent. Just makes a random pick every time that it is
# asked for an action.
class RandomAgent(Agent):

    def getAction(self, state):
        # Get the actions we can try, and remove "STOP" if that is one of them.
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)
        # Random choice between the legal options.
        return api.makeMove(random.choice(legal), legal)

# RandomishAgent
#
# A tiny bit more sophisticated. Having picked a direction, keep going
# until that direction is no longer possible. Then make a random
# choice.
class RandomishAgent(Agent):

    # Constructor
    #
    # Create a variable to hold the last action
    def __init__(self):
         self.last = Directions.STOP
    
    def getAction(self, state):
        # Get the actions we can try, and remove "STOP" if that is one of them.
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)
        # If we can repeat the last action, do it. Otherwise make a
        # random choice.
        if self.last in legal:
            return api.makeMove(self.last, legal)
        else:
            pick = random.choice(legal)
            # Since we changed action, record what we did
            self.last = pick
            return api.makeMove(pick, legal)

# SensingAgent
#
# Doesn't move, but reports sensory data available to Pacman
class SensingAgent(Agent):

    def getAction(self, state):

        # Demonstrates the information that Pacman can access about the state
        # of the game.

        # What are the current moves available
        legal = api.legalActions(state)
        print "Legal moves: ", legal

        # Where is Pacman?
        pacman = api.whereAmI(state)
        print "Pacman position: ", pacman

        # Where are the ghosts?
        print "Ghost positions:"
        theGhosts = api.ghosts(state)
        for i in range(len(theGhosts)):
            print theGhosts[i]

        # How far away are the ghosts?
        print "Distance to ghosts:"
        for i in range(len(theGhosts)):
            print util.manhattanDistance(pacman,theGhosts[i])

        # Where are the capsules?
        print "Capsule locations:"
        print api.capsules(state)
        
        # Where is the food?
        print "Food locations: "
        print api.food(state)

        # Where are the walls?
        print "Wall locations: "
        print api.walls(state)
        
        # getAction has to return a move. Here we pass "STOP" to the
        # API to ask Pacman to stay where they are.
        return api.makeMove(Directions.STOP, legal)
        
        
# GoWestAgent
#
# Always try to go west if possible, otherwise choose random. 
class GoWestAgent(Agent):

    def getAction(self, state):
        # Get the actions we can try, and remove "STOP" if that is one of them.
        legal = api.legalActions(state)
        if Directions.WEST in legal:
            return api.makeMove(Directions.WEST, legal)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)
        # Random choice between the legal options.
        return api.makeMove(random.choice(legal), legal)


# HungryAgent
#
# Moves towards closest food 
class HungryAgent(Agent):

    def getAction(self, state):
        legal = api.legalActions(state)
        food = api.food(state)
        location = api.whereAmI(state)
        closest = None
        distance_to_closest = float('inf')
        for capsule in food:
             distance = util.manhattanDistance(location, capsule)
             if distance < distance_to_closest:
                 distance_to_closest = distance
                 closest = capsule
        directions = getDirectionsTo(closest, location)
        print( location, directions, closest, distance_to_closest)
        for direction in directions:
            if direction in legal:
                return api.makeMove(direction, legal)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)
        # Random choice between the legal options.
        return api.makeMove(random.choice(legal), legal)



# CornerSeekingAgent
#
# Moves towards the four corners of the environment
class CornerSeekingAgent(Agent):

    def __init__(self):
        self.been = set()
        self.target = None
        self.direction = Directions.STOP

    def getAction(self, state):
        location = api.whereAmI(state)
        self.been.add(location)
        corners = api.corners(state)
        legal = api.legalActions(state)
        if location == self.target or not self.target:
            unseen_corners = [corner for corner in corners if corner not in self.been]
            if any(unseen_corners):
                self.target = unseen_corners[0]
            else:
                self.target = None
        if self.target:
            print(self.target)
            directions = getDirectionsTo(self.target, location)
            if self.direction in directions and self.direction in legal:
                return api.makeMove(self.direction, legal)
            for direction in directions:
                if direction in legal and nextLocation(direction, location) not in self.been:
                    self.direction = direction
                    return api.makeMove(direction, legal)
            for direction in directions:
                if direction in legal:
                    self.direction = direction
                    return api.makeMove(direction, legal)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        for direction in legal:
            print(direction, self.been, nextLocation(direction, location))
            if nextLocation(direction, location) not in self.been:
                self.direction = direction
                return api.makeMove(direction, legal)
        # Random choice between the legal options.
        random_direction = random.choice(legal)
        self.direction = random_direction
        return api.makeMove(random_direction, legal)


def getDirectionsTo(target, location):
    directions = []
    if target[0] - location[0] > 0:
        directions.append(Directions.EAST)
    elif target[0] - location[0] < 0:
        directions.append(Directions.WEST)
    if target[1] - location[1] > 0:
        directions.append(Directions.NORTH)
    elif target[1] - location[1] < 0:
        directions.append(Directions.SOUTH)
    return directions


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


class SurvivalAgent(Agent):

    def getAction(self, state):
        ghosts = api.ghosts(state)
        # If direction with no ghosts in legal go there


        # Else go away from closest ghost
        return True