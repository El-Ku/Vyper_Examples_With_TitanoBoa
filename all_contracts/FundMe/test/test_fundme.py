# import libraries
import eth.exceptions  
import boa
import pytest

# import the constants defined in the conftest file
from conftest import ADMIN, SEND_AMOUNT
from conftest import USER0, USER1, USER2, USER3

# an internal function for depositing ether to the fund_me contract and checking if all went well
def deposit(contract, user, amount):
    boa.env.set_balance(user, amount)  # set the balance of an address with `amount`
    balBefore = contract.get_user_balance(user)  
    with boa.env.prank(user):   # prank the given address as the caller
        contract.fund_contract(value=amount)  # call the function with msg.value=amount
    balAfter = contract.get_user_balance(user)
    assert balAfter-balBefore == amount
    
# Test if the contracts were deployed correctly   
def test_init(oracle_impl, fund_me):
    assert fund_me.get_oracle() == oracle_impl.address
    assert fund_me.get_owner() == ADMIN

# Test for reverts for a zero deposit
def test_deposit_zero_amount(fund_me):
	with boa.reverts("msg.value cannot be zero"):   # the next statement should revert with the given error message.
	    fund_me.fund_contract()   #msg.value=0 here

# Test for reverts for a very small deposit
def test_deposit_small_amount(fund_me):
    boa.env.set_balance(USER0, 10**15)
    with boa.env.prank(USER0):
        with boa.reverts("Not enough deposit amount"):
            fund_me.fund_contract(value=10**15)  #send 0.001 ether
    
# Each deposit is checked for its correctness in the _deposit internal function
def test_correct_deposit(fund_me):
    # Do a deposit of 1 eth
    initial_user_balance = fund_me.get_user_balance(USER0)
    deposit(fund_me, USER0, SEND_AMOUNT)
    # Do one more deposit and make sure the user balance is doubled.
    deposit(fund_me, USER0, SEND_AMOUNT)
    final_user_balance = fund_me.get_user_balance(USER0)
    assert final_user_balance-initial_user_balance == 2*SEND_AMOUNT
    
# Try to send funds directly to the contract. Must revert as the fund_me contract doesnt implement a __default__ payable function
def test_deposit_via_default_function(fund_me):
    assert boa.env.get_balance(fund_me.address) == 0 
    boa.env.set_balance(USER0, SEND_AMOUNT)
    with boa.env.prank(USER0):
        with pytest.raises(eth.exceptions.Revert):  # makes sure that the call got reverted
            boa.env.raw_call(fund_me.address, value = SEND_AMOUNT)  
    assert boa.env.get_balance(fund_me.address) == 0  # makes sure that the fund_me contract has zero ether in it.
   
# More than MAX_USER_LIST_SIZE depositors cannot deposit before funds are withdrawn by owner
def test_max_unique_depositors_limit(fund_me):
    deposit(fund_me, boa.env.generate_address(), SEND_AMOUNT)  # 1st deposit
    deposit(fund_me, boa.env.generate_address(), SEND_AMOUNT)  # 2nd deposit
    deposit(fund_me, boa.env.generate_address(), SEND_AMOUNT)  # 3rd deposit
    deposit(fund_me, boa.env.generate_address(), SEND_AMOUNT)  # 4th deposit
    deposit(fund_me, boa.env.generate_address(), SEND_AMOUNT)  # 5th deposit
    
    # 6th deposit should revert
    user6 = boa.env.generate_address()
    boa.env.set_balance(user6, SEND_AMOUNT)
    with boa.env.prank(user6):
        with boa.reverts():   # the next statement reverts. No specific error message is specified.
            fund_me.fund_contract(value=SEND_AMOUNT)

# deposit and check if the userList array and the balances are correctly set.
# Checks for view functions are also performed here.
def test_get_list_of_users(fund_me):
    # send some deposit
    deposit(fund_me, USER1, SEND_AMOUNT)
    # send some deposit
    deposit(fund_me, USER2, SEND_AMOUNT)
    # send some deposit(by the previous user a second time)
    deposit(fund_me, USER2, SEND_AMOUNT)
    # send some deposit
    deposit(fund_me, USER3, SEND_AMOUNT)
    
    # check if 3 unique users are registered
    assert fund_me.get_num_users() == 3
    
    # check if the state variables are set properly when depositing
    assert fund_me.get_user_at_index(0) == USER1
    assert fund_me.get_user_balance(USER1) == SEND_AMOUNT
    assert fund_me.get_user_at_index(1) == USER2
    assert fund_me.get_user_balance(USER2) == 2 * SEND_AMOUNT
    assert fund_me.get_user_at_index(2) == USER3
    assert fund_me.get_user_balance(USER3) == SEND_AMOUNT
 
# Only owner should be able to withdraw   
def test_withdraw_by_regular_user(fund_me):
    with boa.env.prank(USER0):   # USER0 trying to withdraw
        with boa.reverts("Only owner can withdraw"):
            fund_me.withdraw()
    
# Owner is able to withdraw the whole contract balance
def test_withdraw_by_owner(fund_me):
    # first do some deposits
    deposit(fund_me, USER1, SEND_AMOUNT)
    deposit(fund_me, USER2, SEND_AMOUNT*2)
    deposit(fund_me, USER3, SEND_AMOUNT*5)
    
    bal_before = boa.env.get_balance(ADMIN)
    with boa.env.prank(ADMIN):
        withdrawn_funds = fund_me.withdraw()
    balAfter = boa.env.get_balance(ADMIN)
    # makes sure all the accounting is done well 
    assert balAfter-bal_before == withdrawn_funds
    assert withdrawn_funds == SEND_AMOUNT*8
    assert boa.env.get_balance(fund_me.address) == 0
    assert fund_me.get_num_users() == 0  # makes sure that the list of user dynArray was reset properly.
    