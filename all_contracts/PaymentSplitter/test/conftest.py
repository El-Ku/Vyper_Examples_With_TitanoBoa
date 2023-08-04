# Some common constants and functions and fixtures for the test files are written here.
import boa
import pytest

import random  # used for creating some random test data

ADMIN = boa.env.generate_address("admin")
USER0 = boa.env.generate_address("user0")
USER1 = boa.env.generate_address("user1")
TOKEN_ADDRESS = boa.env.generate_address("token")
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'
FEE = 10**15  # 0.001 ether
TIME_LOCK_DURATION = 7*24*60*60  # one week in seconds

    
# deploy the splitter contract as a blueprint. 
@pytest.fixture(scope="module")
def blueprint_impl():
    source = boa.load_partial("contracts/PaymentSplitter.vy") 
    blueprint = source.deploy_as_blueprint()
    return blueprint

# deploy the factory contract and pass the splitter blueprint address to it.
@pytest.fixture(scope="module")
def splitter_factory(blueprint_impl):
    with boa.env.prank(ADMIN):
        factory =  boa.load("contracts/PaymentSplitterFactory.vy", blueprint_impl.address, FEE)
        return factory

# deploy an ERC20 contract
@pytest.fixture(scope="module")
def erc20_token():
    with boa.env.prank(ADMIN):
        # def __init__(_name: String[32], _symbol: String[32], _decimals: uint8, supply: uint256):
        _name = "ERC20-Token"
        _symbol = "ERCT"
        _decimals = 18
        supply = 100_000_000 * 10**_decimals
        return boa.load("contracts/ERC20.vy", _name, _symbol, _decimals, supply)

# creates accounts and shares(random values between 10 and 100) of given array size for testing
def create_accts_and_shares(array_size):
    accounts = []
    shares = []
    total_shares = 0
    for i in range(array_size):
        accounts.append(boa.env.generate_address())
        s = random.randint(10,100)
        shares.append(s)
        total_shares += s
    return (accounts, shares, total_shares)