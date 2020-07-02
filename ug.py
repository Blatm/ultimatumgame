#!/usr/bin/python -tt

import sys
from sage.all import *
import cProfile
import time
import datetime
import random
import bisect


############
### Main ###
############

def main():
    pass



###############
### Classes ###
###############

class Person:
    def __init__(self, offer=0.0, accept_thresh=0.0, score=0.0):
        self.offer = offer
        self.accept_thresh = accept_thresh
        self.score = score # not copied

    def copy(self):
        newPerson = Person(self.offer, self.accept_thresh)
        return newPerson
    
    def mutate(self, offer_eps, accept_thresh_eps):
        newPerson = self.copy()
        newPerson.offer += random.uniform(-offer_eps, offer_eps)
        newPerson.offer = clamp(newPerson.offer, 0.0, 1.0)
        newPerson.accept_thresh += random.uniform(-accept_thresh_eps, accept_thresh_eps)
        newPerson.accept_thresh = clamp(newPerson.accept_thresh, 0.0, 1.0)
        return newPerson
    
    def utility(self, val):
        # val between 0 and 1 please
        #return val # Identity function
        return sqrt(val)

    def write_to_file(self, filename):
        f = open(filename,'a')
        f.write('offer: '+str(self.offer)+'\n')
        f.write('accept_thresh: '+str(self.accept_thresh)+'\n')
        f.write('score: '+str(self.score)+'\n')
        f.close()


class Population:
    def __init__(self, people=[], offer_eps=0.01, accept_thresh_eps=0.01):
        self.people = people
        self.offer_eps = offer_eps
        self.accept_thresh_eps = accept_thresh_eps
    
    def copy(self):
        newPop = Population(self.people, self.offer_eps, self.accept_thresh_eps)
        return newPop
    
    def get_pairings(self):
        tups = []
        shuffled_pop = random.sample(self.people, len(self.people))
        for i in range(len(shuffled_pop)/2):
            offerer = shuffled_pop[2*i]
            accepter = shuffled_pop[2*i+1]
            tups.append((offerer,accepter))
        return tups

    def set_all_scores(self, scoreval):
        for person in self.people:
            person.score = scoreval

    def play_round(self, scoreval=0.0):
        self.set_all_scores(scoreval)
        tups = self.get_pairings()
        for tup in tups:
            play(tup)

    def get_total_utility(self):
        total = 0.0
        for person in self.people:
            total += person.utility(person.score)
        return total

    def get_utility_partial_sums(self):
        partial_sums = [0.0]
        for person in self.people:
            last = partial_sums[-1]
            current = person.utility(person.score)
            new = last+current
            partial_sums.append(new)
        return partial_sums
    
    def get_samples(self):
        total_utility = self.get_total_utility()
        samples = []
        for _ in range(len(self.people)):
            newsample = random.uniform(0.0, total_utility)
            samples.append(newsample)
        return samples

    def sample_to_person(self, sample, partial_sums):
        i = bisect.bisect(partial_sums, sample)-1
        person = self.people[i]
        return person
    
    def get_new_people(self):
        new_people = []
        samples = self.get_samples()
        partial_sums = self.get_utility_partial_sums()
        for sample in samples:
            new_person = self.sample_to_person(sample, partial_sums)
            new_people.append(new_person)
        return new_people

    def mutate(self, in_place=True):
        new_people = []
        for person in self.people:
            new_person = person.mutate(self.offer_eps, self.accept_thresh_eps)
            new_people.append(new_person)
        if in_place:
            self.people = new_people
        else:
            return new_people
        
    def get_next_generation(self):
        new_people = self.get_new_people()
        new_population = self.copy()
        new_population.people = new_people
        new_population.mutate()
        return new_population

    def advance_generations(self, numgens, record_interval=None):
        pop_list = []
        pop = self
        for i in range(numgens):
            pop.play_round()
            pop = pop.get_next_generation()
            if record_interval is not None:
                if (i%record_interval) == 0:
                    pop_list.append(pop)
        pop_list.append(pop)
        return pop_list

    def get_dists(self):
        offer_list = []
        accept_thresh_list = []
        for person in self.people:
            offer_list.append(person.offer)
            accept_thresh_list.append(person.accept_thresh)
        return (offer_list, accept_thresh_list)

    def write_to_file(self, filename, write_params=True):
        if write_params:
            f = open(filename,'a')
            f.write('offer_eps: '+str(self.offer_eps)+'\n')
            f.write('accept_thresh_eps: '+str(self.accept_thresh_eps)+'\n')
            f.close()
        for person in self.people:
            person.write_to_file(filename)
        f = open(filename,'a')
        f.write('\n')
        f.close()


#################
### Functions ###
#################

def clamp(val, minval, maxval):
    if val < minval:
        return minval
    if val > maxval:
        return maxval
    return val


def play(player_tup):
    (offerer, accepter) = player_tup
    if offerer.offer >= accepter.accept_thresh:
        offerer.score += 1.0 - offerer.offer
        accepter.score += offerer.offer
    

def get_initial_people(numpeople):
    people = []
    for _ in range(numpeople):
        offer = random.random()
        accept_thresh = random.random()
        new_person = Person(offer, accept_thresh)
        people.append(new_person)
    return people


def get_gens(numpeople, numgenerations, record_interval=10**2, eps=0.01):
    initial_people = get_initial_people(numpeople)
    starting_pop = Population(initial_people, offer_eps=eps, accept_thresh_eps=eps)
    generations = starting_pop.advance_generations(numgenerations, record_interval=record_interval)
    return generations


def gens_to_averages(generations):
    avg_offer_list = []
    avg_accept_thresh_list = []
    for i in range(len(generations)):
        (offer_list, accept_thresh_list) = generations[i].get_dists()
        avg_offer = sum(offer_list)/len(offer_list)
        avg_accept_thresh = sum(accept_thresh_list)/len(accept_thresh_list)
        avg_offer_list.append((i,avg_offer))
        avg_accept_thresh_list.append((i,avg_accept_thresh))
    return (avg_offer_list, avg_accept_thresh_list)


#This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    if '-profile' in sys.argv:
        cProfile.run('main()')
    else:
        main()
