# This file tests factory contract and its functions

# import libraries
import boa
import pytest

# import the constants defined in the conftest file
from conftest import ADMIN, USER0, FEE

# Test if the contracts were deployed correctly   
def test_init(blueprint_impl, splitter_factory):
    assert splitter_factory.i_owner() == ADMIN
    assert splitter_factory.i_payment_splitter_blueprint() == blueprint_impl.address
    assert splitter_factory.protocol_fee() == FEE

# Normal user trying to change the protocol fee should revert
def test_change_fee_by_user(splitter_factory):
    new_fee = 10**16
    with boa.env.prank(USER0):
        with boa.reverts("only owner can request a fee change"):
            splitter_factory.request_to_set_protocol_fee(new_fee)

# Test for changing fee in factory before timelock period
def test_change_fee_before_timelock(splitter_factory):
    new_fee = 10**16
    # first admin requests the protocol fee to be changed
    with boa.env.prank(ADMIN):
        splitter_factory.request_to_set_protocol_fee(new_fee)
    current_block_number = boa.env.vm.state.block_number
    boa.env.time_travel(blocks = 9)
    # only 9 blocks have gone past instead of 10, and someone tries to confirm the fee change. but it will revert
    with boa.reverts("time lock period to change fee is not yet over"):
        splitter_factory.set_protocol_fee()

# Test for changing fee in factory after timelock period
def test_change_fee_after_timelock(splitter_factory):
    assert splitter_factory.protocol_fee() == FEE
    new_fee = 10**16
    with boa.env.prank(ADMIN):
        splitter_factory.request_to_set_protocol_fee(new_fee)
    current_block_number = boa.env.vm.state.block_number
    boa.env.time_travel(blocks = 10)  # we have gone past timelock period.
    splitter_factory.set_protocol_fee()
    assert splitter_factory.protocol_fee() == new_fee
