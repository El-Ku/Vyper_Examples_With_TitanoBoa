# @version 0.3.9
"""
@title FundMe Contract in Vyper
@author ElKu
@license MIT
@notice Users are able to fund the contract with native tokens which can be withdrawn by the owner of the contract
"""

interface AggregatorV3Interface:
    # There are more functions here, but I didnt include them here because I am not using it in this project
    def latestRoundData() -> (uint80, int256, uint256, uint256, uint80): view

i_owner: immutable(address)
i_oracle: immutable(address)
MIN_USD_DEPOSIT: constant(uint256) = 50 * 10**18    # protection against small dummy deposits. Avoid DoS attack.
MAX_USER_LIST_SIZE: constant(uint256) = 5  #after MAX_USER_LIST_SIZE users, no one will be able to deposit before owner withdraws funds
userList: DynArray[address, MAX_USER_LIST_SIZE]
userBal: HashMap[address, uint256]

# constructor function
@external
def __init__(oracle: address):
	i_owner = msg.sender
	i_oracle = oracle

@external
@payable
def fund_contract():
    """
    @notice Any user can send funds to the contract
    @dev The msg.value should be greater than `MIN_USD_DEPOSIT`
    """
    assert msg.value > 0, "msg.value cannot be zero"
    amountInDollars: uint256 = self._get_price_in_usd() * msg.value / 10**18   #convert ether to usd
    assert amountInDollars >= MIN_USD_DEPOSIT, "Not enough deposit amount"
    if(self.userBal[msg.sender] == 0):  #append user address only if he hasnt deposited before
        # not checking if we have reached the max dynArray size because if it has the next statement will revert
        self.userList.append(msg.sender)
    self.userBal[msg.sender] += msg.value  # keep track of how much a user has deposited

@external
def withdraw() -> uint256:
    """
    @notice Allows owner to withdraw deposited funds.
    @dev The deposit information so far is reset.
    """
    assert msg.sender == i_owner, "Only owner can withdraw"
    assert self.balance > 0, "No funds to withdraw"
	# clear balances
    #user: address = 0
    for user in self.userList:
        self.userBal[user] = 0   #resets how much a user has deposited
    self.userList = empty(DynArray[address, MAX_USER_LIST_SIZE])  # clear the list of depositors
    availableFunds: uint256 = self.balance
    send(msg.sender, availableFunds)  # send the whole contract balance to owner
    return availableFunds

@internal
@view
def _get_price_in_usd() -> uint256:
    """
    @dev Internal function to get the price of eth in usd and to convert it into 18 decimals.
    """
    price: int256 = 0
    price = AggregatorV3Interface(i_oracle).latestRoundData()[1]
    return convert(price * 10**(18 - 8), uint256)

#################   View functions.    #################

@external
@view
def get_owner() -> address:
    """
    @notice Gets the owner of this contract
    @return The owner address
    """
    return i_owner

@external
@view
def get_user_balance(user: address) -> uint256:
    """
    @notice Gets the deposit amount of a particular user
    @param user address of the user who's deposit amount you seek
    @return User deposit
    """
    return self.userBal[user]


@external
@view
def get_user_at_index(index: uint256) -> address:
    """
    @notice Get the list of depositers 
    @return List of all depositer's addresses as an array.
    """
    return self.userList[index]

@external
@view
def get_num_users() -> uint256:
    """
    @notice Get the number of unique depositers 
    @return the number of unique depositers 
    """
    return len(self.userList)


@external
@view
def get_oracle() -> address:
    """
    @notice Gets the price oracle address
    @return The price oracle address
    """
    return i_oracle

