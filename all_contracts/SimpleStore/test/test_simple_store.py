import boa
import pytest

from conftest import INITIAL_VALUE 

def testGet(deploy):
	assert deploy.get() == INITIAL_VALUE

#Store a number and see if its successfully stored
def testStore(deploy):
	assert deploy.get() == INITIAL_VALUE  # check once again
	deploy.store(1000)  # store a number 1000 in the storage variable
	assert deploy.get() == 1000  # checks if it was correctly stored

# Just to check that fixture ran again after the testStore test stores a different number.
def testStoreFixture(deploy):
	assert deploy.get() == INITIAL_VALUE  