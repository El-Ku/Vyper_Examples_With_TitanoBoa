import boa
import pytest

ADMIN = boa.env.generate_address("admin")
USER0 = boa.env.generate_address("user0")
USER1 = boa.env.generate_address("user1")
USER2 = boa.env.generate_address("user2")
USER3 = boa.env.generate_address("user3")

SEND_AMOUNT = 10**18
    

@pytest.fixture(scope="session")
def oracle_impl():
    with boa.env.prank(ADMIN):
        return boa.load("contracts/AggregatorV3Interface.vy")


@pytest.fixture(scope="session")
def fund_me(oracle_impl):
    with boa.env.prank(ADMIN):
        return boa.load("contracts/FundMe.vy", oracle_impl.address)
