# This file tests Splitter contract(deployed by the factory contract) and its functions

# import libraries
import boa
import pytest

# import the constants defined in the conftest file
from conftest import ADMIN, USER0, USER1, FEE, TIME_LOCK_DURATION
from conftest import create_accts_and_shares
from conftest import ZERO_ADDRESS

ENABLE_PRINT_LOGS = False   # Make this true if you want the log's to get printed

PAY_SPLITTER_DEPLOYER = boa.load_partial("contracts/PaymentSplitter.vy")

# helper function to check that a splitter contract is created properly. 
def verify_splitter_creation(pay_splitter_addr, factory_address, user, accounts, shares, _token, _amount, total_shares, value_to_sent) -> bool:
    # these two lines typecast the address of the contract to VyperContract. 
    
    pay_splitter = PAY_SPLITTER_DEPLOYER.at(pay_splitter_addr)  
    assert boa.env.get_balance(pay_splitter.address) == value_to_sent-FEE
    assert pay_splitter.i_total_shares() == total_shares
    for i in range(5):  # checks if accounts and shares are set properly
        acc, sh = pay_splitter.get_info_at_index(i)
        assert accounts[i] == acc
        assert shares[i] == sh
    assert pay_splitter.i_owner() == user
    assert pay_splitter.i_token() == _token
    assert pay_splitter.i_total_eth_to_split() == value_to_sent - FEE
    assert pay_splitter.i_total_tokens_to_split() == _amount

# helper function to print the event logs. Can be disabled.
def print_logs(logs):
    if(ENABLE_PRINT_LOGS == False):
        return
    size = len(logs)
    for i in range(size):
        print('\n\n',logs[i])

# helper function to verify that the account holders are able to withdraw their share of funds from the splitter contract.
def verify_getting_paid(accounts, shares, total_shares, pay_splitter_addr, num_splitters, erc20_token, value_to_sent, _amount, skip_last):
    pay_splitter = PAY_SPLITTER_DEPLOYER.at(pay_splitter_addr)
    if(skip_last == 1):  # the last person doesnt call the get_paid function. 
        num_splitters -= 1  
    for i in range(num_splitters):
        user = accounts[i]
        with boa.env.prank(user):  #each user calls the get_paid function and their pre and post balances are checked for correctness
            old_balance_eth = boa.env.get_balance(user) 
            old_balance_token = erc20_token.balanceOf(user)
            assert pay_splitter.get_paid() == True
            new_balance_eth = boa.env.get_balance(user) 
            new_balance_token = erc20_token.balanceOf(user)
            actual_user_share_eth = (value_to_sent-FEE)*shares[i] / total_shares
            actual_user_share_tokens = _amount*shares[i] / total_shares
            assert old_balance_eth + actual_user_share_eth == new_balance_eth
            assert old_balance_token + actual_user_share_tokens == new_balance_token
            print_logs(pay_splitter.get_logs())
    if(skip_last != 1):  # splitter contract should have zero tokens and eth if everyone withdrew their share of funds
        assert erc20_token.balanceOf(pay_splitter_addr) == 0
        assert boa.env.get_balance(pay_splitter_addr) == 0 
    
######################## Tests begin now.  ##############################################

# Send only FEE-1 eth as msg.value. This will revert because of the underflow operation in factory contract
def test_create_pay_splitter_with_less_eth(splitter_factory):
    assert splitter_factory.get_nonces(USER0) == 0
    num_splitters = 5
    boa.env.set_balance(USER0, FEE)
    accounts, shares, total_shares = create_accts_and_shares(array_size=num_splitters)
    with boa.env.prank(USER0):
        with boa.reverts():
            pay_splitter_addr = splitter_factory.create_pay_splitter(accounts, shares, ZERO_ADDRESS, 0, value = FEE-1)

# _amount is set to zero. But enough eth is send and its a multiple of total_shares. so wont revert
def test_create_pay_splitter_with_enough_eth(splitter_factory):
    assert splitter_factory.get_nonces(USER0) == 0
    num_splitters = 5
    _amount = 0
    _token = ZERO_ADDRESS
    accounts, shares, total_shares = create_accts_and_shares(array_size=num_splitters)
    value_to_sent = FEE + total_shares*1000
    boa.env.set_balance(USER0, value_to_sent)
    with boa.env.prank(USER0):
        pay_splitter_addr = splitter_factory.create_pay_splitter(accounts, shares, _token, _amount, value=value_to_sent)
        verify_splitter_creation(pay_splitter_addr, splitter_factory, USER0, accounts, shares, _token, _amount, total_shares, value_to_sent)
        print_logs(splitter_factory.get_logs())
        assert splitter_factory.get_nonces(USER0) == 1  # check that nonce incremented by 1

# makes the eth available to split not exactly divisible by total_shares.
def test_create_pay_splitter_with_incorrect_eth(splitter_factory):
    assert splitter_factory.get_nonces(USER0) == 0
    num_splitters = 5
    _amount = 0
    _token = ZERO_ADDRESS
    accounts, shares, total_shares = create_accts_and_shares(array_size=num_splitters)
    value_to_sent = FEE + total_shares*1000 - 10 #makes the eth available to split not exactly divisible by total_shares.
    boa.env.set_balance(USER0, value_to_sent)
    with boa.env.prank(USER0):
        with boa.reverts():
            pay_splitter_addr = splitter_factory.create_pay_splitter(accounts, shares, _token, _amount, value=value_to_sent)

# Check if the token transfers happen to splitter contract correctly.
def test_token_transfer_at_splitter_creation(splitter_factory, erc20_token):
    assert splitter_factory.get_nonces(USER0) == 0
    num_splitters = 5
    _token = erc20_token.address
    accounts, shares, total_shares = create_accts_and_shares(array_size=num_splitters)
    _amount = total_shares*1000_000
    value_to_sent = FEE + total_shares*1000 
    with boa.env.prank(ADMIN):  # admin sends some tokens to USER0 for testing.
        assert erc20_token.transfer(USER0, _amount) == True
        assert erc20_token.balanceOf(USER0) == _amount
    boa.env.set_balance(USER0, value_to_sent)
    with boa.env.prank(USER0):
        assert erc20_token.approve(splitter_factory.address, _amount) == True   # user approves factory contract first for erc20 token transfer
        pay_splitter_addr = splitter_factory.create_pay_splitter(accounts, shares, _token, _amount, value=value_to_sent)
        verify_splitter_creation(pay_splitter_addr, splitter_factory, USER0, accounts, shares, _token, _amount, total_shares, value_to_sent)
        print_logs(splitter_factory.get_logs())
        assert splitter_factory.get_nonces(USER0) == 1
        assert erc20_token.balanceOf(USER0) == 0
        assert erc20_token.balanceOf(pay_splitter_addr) == _amount

# Check if a user can create more than one splitter contract, even with the same settings.
def test_splitter_creation_twice(splitter_factory, erc20_token):
    assert splitter_factory.get_nonces(USER0) == 0
    num_splitters = 5
    _token = erc20_token.address
    accounts, shares, total_shares = create_accts_and_shares(array_size=num_splitters)
    _amount = total_shares*1000_000
    value_to_sent = FEE + total_shares*1000 
    # first splitter contract creation
    with boa.env.prank(ADMIN):
        assert erc20_token.transfer(USER0, _amount) == True
        assert erc20_token.balanceOf(USER0) == _amount
    boa.env.set_balance(USER0, value_to_sent)
    with boa.env.prank(USER0):
        assert erc20_token.approve(splitter_factory.address, _amount) == True
        pay_splitter_addr = splitter_factory.create_pay_splitter(accounts, shares, _token, _amount, value=value_to_sent)
        verify_splitter_creation(pay_splitter_addr, splitter_factory, USER0, accounts, shares, _token, _amount, total_shares, value_to_sent)
        print_logs(splitter_factory.get_logs())
        assert splitter_factory.get_nonces(USER0) == 1   # nonce incremented 
        assert erc20_token.balanceOf(USER0) == 0
        assert erc20_token.balanceOf(pay_splitter_addr) == _amount
    # second splitter contract creation
    with boa.env.prank(ADMIN):
        assert erc20_token.transfer(USER0, _amount) == True
        assert erc20_token.balanceOf(USER0) == _amount
    boa.env.set_balance(USER0, value_to_sent)
    with boa.env.prank(USER0):
        assert erc20_token.approve(splitter_factory.address, _amount) == True
        pay_splitter_addr = splitter_factory.create_pay_splitter(accounts, shares, _token, _amount, value=value_to_sent)
        verify_splitter_creation(pay_splitter_addr, splitter_factory, USER0, accounts, shares, _token, _amount, total_shares, value_to_sent)
        print_logs(splitter_factory.get_logs())
        assert splitter_factory.get_nonces(USER0) == 2  # nonce incremented again
        assert erc20_token.balanceOf(USER0) == 0
        assert erc20_token.balanceOf(pay_splitter_addr) == _amount

# The splitter contract is created successfully and shareholders got paid properly.
def test_creation_and_getting_paid(splitter_factory, erc20_token):
    assert splitter_factory.get_nonces(USER0) == 0
    num_splitters = 5
    _token = erc20_token.address
    accounts, shares, total_shares = create_accts_and_shares(array_size=num_splitters)
    _amount = total_shares*1000_000
    value_to_sent = FEE + total_shares*1000
    with boa.env.prank(ADMIN):
        assert erc20_token.transfer(USER0, _amount) == True
        assert erc20_token.balanceOf(USER0) == _amount
    boa.env.set_balance(USER0, value_to_sent)
    with boa.env.prank(USER0):
        assert erc20_token.approve(splitter_factory.address, _amount) == True
        pay_splitter_addr = splitter_factory.create_pay_splitter(accounts, shares, _token, _amount, value=value_to_sent)
        verify_splitter_creation(pay_splitter_addr, splitter_factory, USER0, accounts, shares, _token, _amount, total_shares, value_to_sent)
        print_logs(splitter_factory.get_logs())
        assert splitter_factory.get_nonces(USER0) == 1
        assert erc20_token.balanceOf(USER0) == 0
        assert erc20_token.balanceOf(pay_splitter_addr) == _amount
    verify_getting_paid(accounts, shares, total_shares, pay_splitter_addr, num_splitters, erc20_token, value_to_sent, _amount, 0)

# A user tries to get paid twice. But it reverts
def test_trying_to_get_paid_twice(splitter_factory, erc20_token):
    assert splitter_factory.get_nonces(USER0) == 0
    num_splitters = 5
    _token = erc20_token.address
    accounts, shares, total_shares = create_accts_and_shares(array_size=num_splitters)
    _amount = total_shares*1000_000
    value_to_sent = FEE + total_shares*1000 #makes the eth available to split not exactly divisible by total_shares.
    with boa.env.prank(ADMIN):
        assert erc20_token.transfer(USER0, _amount) == True
        assert erc20_token.balanceOf(USER0) == _amount
    boa.env.set_balance(USER0, value_to_sent)
    with boa.env.prank(USER0):
        assert erc20_token.approve(splitter_factory.address, _amount) == True
        pay_splitter_addr = splitter_factory.create_pay_splitter(accounts, shares, _token, _amount, value=value_to_sent)
        verify_splitter_creation(pay_splitter_addr, splitter_factory, USER0, accounts, shares, _token, _amount, total_shares, value_to_sent)
        print_logs(splitter_factory.get_logs())
        assert splitter_factory.get_nonces(USER0) == 1
        assert erc20_token.balanceOf(USER0) == 0
        assert erc20_token.balanceOf(pay_splitter_addr) == _amount
    # tries to get paid twice
    pay_splitter = PAY_SPLITTER_DEPLOYER.at(pay_splitter_addr)
    user = accounts[0]
    with boa.env.prank(user):
        assert pay_splitter.get_paid() == True  # first time calling get_paid()
        with boa.reverts("User has been already paid"):
            pay_splitter.get_paid()  # 2nd time calling get_paid(), but now it reverts

# After the lock period is over owner can withdraw the unpaid leftover funds to himself
def test_withdraw_after_lock_period(splitter_factory, erc20_token):
    assert splitter_factory.get_nonces(USER0) == 0
    num_splitters = 5
    _token = erc20_token.address
    accounts, shares, total_shares = create_accts_and_shares(array_size=num_splitters)
    _amount = total_shares*1000_000
    value_to_sent = FEE + total_shares*1000 #makes the eth available to split not exactly divisible by total_shares.
    with boa.env.prank(ADMIN):
        assert erc20_token.transfer(USER0, _amount) == True
        assert erc20_token.balanceOf(USER0) == _amount
    boa.env.set_balance(USER0, value_to_sent)
    with boa.env.prank(USER0):
        assert erc20_token.approve(splitter_factory.address, _amount) == True
        pay_splitter_addr = splitter_factory.create_pay_splitter(accounts, shares, _token, _amount, value=value_to_sent)
        verify_splitter_creation(pay_splitter_addr, splitter_factory, USER0, accounts, shares, _token, _amount, total_shares, value_to_sent)
        print_logs(splitter_factory.get_logs())
        assert splitter_factory.get_nonces(USER0) == 1
        assert erc20_token.balanceOf(USER0) == 0
        assert erc20_token.balanceOf(pay_splitter_addr) == _amount

    # last account holder doesnt withdraw his funds.
    verify_getting_paid(accounts, shares, total_shares, pay_splitter_addr, num_splitters, erc20_token, value_to_sent, _amount, 1) 

    pay_splitter = PAY_SPLITTER_DEPLOYER.at(pay_splitter_addr)

    with boa.env.prank(USER1):
        with boa.reverts("Only owner can withdraw"):
            pay_splitter.withdraw()

    with boa.env.prank(USER0):
        with boa.reverts("Too early to withdraw funds"):
            pay_splitter.withdraw()

    boa.env.time_travel(TIME_LOCK_DURATION+100)   # fast forward block time past TIME_LOCK_DURATION
    with boa.env.prank(USER0):
        old_balance_eth = boa.env.get_balance(USER0) 
        old_balance_token = erc20_token.balanceOf(USER0)
        assert pay_splitter.withdraw() == True
        new_balance_eth = boa.env.get_balance(USER0) 
        new_balance_token = erc20_token.balanceOf(USER0)
        assert old_balance_eth < new_balance_eth
        assert old_balance_token < new_balance_token
        assert boa.env.get_balance(pay_splitter_addr) == 0
        assert erc20_token.balanceOf(pay_splitter_addr) == 0
        print_logs(pay_splitter.get_logs())

        