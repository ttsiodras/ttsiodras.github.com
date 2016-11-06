#!/usr/bin/env python
import random

# A sickness with no symptoms has appeared in the general population:
# Chances of getting it, are one in ten thousand.
#
# Whoever has it, dies within a year.
#
# Naturally, people want to know if they are sick or not - to make sure
# their affairs are in order, fix their wills and testaments... say their
# farewells to their loved ones, and come to terms with their fate.
#
# Scientists have devised a test, which can show whether you have the 
# sickness or not, with an accuracy of 99%.
# 
# You just took the test - and you are told that it is positive.
#
# Should you start taking care of your post-mortem affairs?
# Or is it too soon?
#
# Don't read the rest, before you think about this.
# Be honest - no cheating!
#
#
#
# Well, let's assume that we have one million test subjects.
# One in ten thousand of them will be sick, which means that...
#
#     1.000.000 x 1 / 10.000 = 100 sick people
#
# ...100 of them will be sick - and 999.900 will be healthy.
# Now we perform the test on all one million of them: remember,
# the test is 99% accurate, so...
#
#                    1.000.000 people
#                     /           \
#                    /             \
#                   /               \
#              100 sick      999.900 healthy
#                 /\             /     \
#                /  \           /       \
#          99 pos   1 neg  9.999 pos  989.901 neg
#
# ...out of the 100 sick, it will give a positive result to 99,
# and miss only one, who will get a negative. Out of the 999.900
# healthy ones, 1% (that is, 9.999) will get a false positive,
# and the rest (999.900 - 9.999 = 989.901) will get a correct,
# negative result.
#
# So, grouping all who got positive results, you have:
#
# - 99 that are REALLY sick
# - and 9.999 that are healthy
#
# So, given the fact that the result is positive, your chance
# of ACTUALLY being sick, is:
#
#                                            99
#  P(I am sick if my test is positive) = ---------
#                                        99 + 9999
#
# ...which amounts to a little less than 1%.
# In other words, keep partying!
#
#
# The above is a simple example of the Bayes theorem, whose
# formal application is the following:
# ( the symbol '|' means 'given' )
#
#                          P(Sick)*P(TestPositive|Sick)
# P(Sick|TestPositive) = ------------------------------
#                                P(TestPositive)
#
#                     P(Sick)*P(TestPositive|Sick)
# =  -----------------------------------------------------------------
#    P(Sick)*P(TestPositive|Sick) + P(Healthy)*P(TestPositive|Healthy)
#
#               (1/10000)*0.99
# =  ------------------------------------- = 0.0098039215
#      (1/10000)*0.99 + (9999/10000)*0.01
#
# What follows below, is an experimental verification, 
# via a simple Python reproduction of the experiment.

# First, a helper function:
# When passed a number between 0 and 100, this function
# returns True with exactly the requested chance
# e.g. BoolProb(40) would return True with a 40% chance
#
def BoolProb(x):
    return random.random() < x/100.

# And now, the complete experiment:

# The experiment's sample size
SampleSize = 10000000
# How many positive results we got
PositiveTests = 0
# How many of the positive results were actually sick
PositiveTestAndSick = 0

for i in xrange(0, SampleSize):
    sick = BoolProb(0.01) # 1 in 10.000 => 0.01
    if sick:
	# If you are sick, you get a 99% chance of a positive
	testResultPositive = BoolProb(99) 
    else:
	# If you are healthy, you get a 1% chance of a positive
	testResultPositive = BoolProb(1)

    # Count the results
    if testResultPositive:
	PositiveTests += 1
        if sick:
	    PositiveTestAndSick += 1

print "Chance of being sick if test is positive:", \
    float(PositiveTestAndSick)/PositiveTests
