import boa
import pytest

INITIAL_VALUE = 1234

@pytest.fixture(scope = "function")  # its "function" by default. No need to mention it really.
def deploy():
	yield boa.load("contracts/SimpleStore.vy", INITIAL_VALUE)
