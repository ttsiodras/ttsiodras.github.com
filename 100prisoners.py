#!/usr/bin/env python
import itertools

# The 100 prisoners problem statement:
#
# The warden places 100 numbers in 100 boxes, at random - with equal
# probability that any number will be in any box. Each convict is assigned
# a number. One by one they enter the room with the boxes, and try to find
# their corresponding number. They can open up to 50 different boxes. Once
# they either find their number or fail, they move on to a different room
# and all of the boxes are returned to exactly how they were before the
# prisoner entered the room.  The prisoners can communicate with each
# other before the game begins, but as soon as it starts they have no way
# to signal to each other. The warden is requiring that all 100 prisoners
# find their numbers!
#
# At first glance, since each of them has 50% chance (0.5), the probability
# of all of them succeeding is (0.5)^100 = .... zero.
#
# And yet, with the approach described below, the chance of success
# (i.e. ALL of them finding their number) is 31.2% !!!
#
# In fact, for N prisoners, with N=2*k, the probability of success is:
#
#            p(success) = 1-(1/M + 1/(M+1) + ... + (1/N))
# where
#            M = N/2 + 1        
#
# So, for N=8:   1-(1/5+1/6+1/7+1/8)      = .36547619047
#     for N=10:  1-(1/6+1/7+1/8+1/9+1/10) = .35436507936
#     for N=100: 1-(1/51+1/52+...+ 1/100) = .31182782069
#
# Brilliant description of the puzzle's solution here:
#   http://www.mast.queensu.ca/~peter/inprocess/prisoners.pdf

def CheckSolution(prisoners, perm):
    for i in xrange(prisoners):
	attempt = 0
	idx = i
	found = False
	while attempt < prisoners/2: # You have N/2 attempts...
	    if perm[idx] == i:  # Look in your box...
		found = True    # you found your number, great!
		break
	    else:
		idx = perm[idx] # else "seek" to the number inside the box
	    attempt += 1
	if not found:
	    return False # This permutation failed, it had a cycle>N/2
    return True # This permutation was a good one...
		
def main():
    for prisoners in xrange(4, 12, 2): # Do the experiment for 4,6,8,10
	total = 0
	success = 0
	for perm in itertools.permutations(xrange(prisoners)):
	    total += 1
	    if CheckSolution(prisoners, perm):
		success += 1
	print "When", prisoners,"prisoners,",
	print "Saved:", success, "/", total,
	print "(%5.2f)" % (100.0*success/total)

if __name__ == "__main__":
    main()
