# @version 0.3.9
"""
@title PaymentSplitter Contract in Vyper
@author ElKu
@license MIT
@notice This contract is deployed by the factory contract by users who wants to split some ether or ERC20 tokens among a set of addresses
"""

from vyper.interfaces import ERC20

TIME_LOCK_DURATION: constant(uint256) = 7*24*60*60  # one week
i_owner: public(immutable(address))
i_created_at: public(immutable(uint256))
i_accounts: immutable(DynArray[address, 100])
i_shares: immutable(DynArray[uint256, 100])
i_total_eth_to_split: public(immutable(uint256))
i_total_tokens_to_split: public(immutable(uint256))
i_token: public(immutable(address))
i_total_shares: public(immutable(uint256))
paid_accounts: HashMap[address, bool]

# events 
event SharesPaid:
	account: indexed(address)
	eth: uint256
	tokens: uint256

event FundsWithdrawn:
	eth: uint256
	tokens: uint256

@external
@payable
def __init__(_owner: address, _accounts: DynArray[address, 100], _shares: DynArray[uint256, 100], _token: address, _amount: uint256):
	"""
     @dev constructor function
     @param _owner address The address which created and funded this contract
     @param _accounts DynArray[address] The addresses which has a share in the contract funds
     @param _shares DynArray[uint256] The shares which decide what part of the funds can be withdrawn by a user
	 @param _token address The ERC20 token address 
	 @param _amount uint256 Amount of ERC20 tokens available to split among the _accounts
    """
	i_token = _token
	assert _owner != empty(address), "owner cant be zero address"
	i_owner = _owner
	assert len(_accounts) == len(_shares), "accounts and shares length doesn't match"
	assert (_token != empty(address) and _amount > 0) or msg.value > 0, "At least payment must be an ERC20 token or ether"
	i_created_at = block.timestamp   # contract creation time
	i_accounts = _accounts
	i_shares = _shares
	i_total_eth_to_split = msg.value
	i_total_tokens_to_split = _amount
	ts: uint256 = 0
	for s in i_shares:
		assert s > 0, "No zero-value shares are allowed"
		ts += s
	i_total_shares = ts  #sum of all shares
	# the ether or tokens present in the pool must be perfectly divisible by total_shares.
	if msg.value >0:
		assert (msg.value/i_total_shares) * i_total_shares == msg.value, "Splitter might leave dust ether"
	if _amount > 0:
		assert (_amount/i_total_shares) * i_total_shares == _amount, "Splitter might leave dust tokens"

@external
def get_paid() -> bool:
	"""
     @dev Used by account's to claim their part of the funds.
	 @return bool, True if account was successfully paid out
    """
	assert not self.paid_accounts[msg.sender], "User has been already paid"
	i: uint256 = 0
	acc_share: uint256 = 0
	# find out the shares to the corresponding msg.sender and mark him as paid
	for account in i_accounts:
		if msg.sender == account:
			acc_share = i_shares[i]
			self.paid_accounts[msg.sender] = True
			break
		i += 1
	eth: uint256 = 0
	tokens: uint256 = 0
	if i_total_eth_to_split > 0:
		eth = i_total_eth_to_split*acc_share/i_total_shares
		send(msg.sender, eth)  # send ether if its more than zero.
	if i_total_tokens_to_split > 0:
		tokens = i_total_tokens_to_split*acc_share/i_total_shares
		assert ERC20(i_token).transfer(msg.sender, tokens) == True # send erc20 tokens if its more than zero.
	log SharesPaid(msg.sender, eth, tokens)  # Event
	return True

@external
def withdraw() -> bool:
	"""
     @dev Used by account's owner to withdraw back funds which are in the contract which hasnt been taken even after the TIME_LOCK_DURATION
	 @return bool, True if funds were successfully sent back to the owner
    """
	assert i_owner == msg.sender, "Only owner can withdraw"
	assert block.timestamp >= i_created_at + TIME_LOCK_DURATION, "Too early to withdraw funds"
	log FundsWithdrawn(self.balance, ERC20(i_token).balanceOf(self))   # Event 
	if(self.balance > 0):
		send(i_owner, self.balance)
	if(ERC20(i_token).balanceOf(self) > 0):
		assert ERC20(i_token).transfer(i_owner, ERC20(i_token).balanceOf(self)) == True
	return True

@external
@view
def get_account_share(acc: address) -> (uint256, uint256):
	"""
     @dev Find out how much funds can be withdrawn by a particular address
	 @return uint256, amount of ether he can withdraw
	 @return uint256, amount of tokens he can withdraw
    """
	i: uint256 = 0
	acc_share: uint256 = 0
	for account in i_accounts:
		if acc == account:
			acc_share = i_shares[i]
			break
		i += 1
	eth_share: uint256 = i_total_eth_to_split*acc_share/i_total_shares
	token_share: uint256 = i_total_tokens_to_split*acc_share/i_total_shares
	return (eth_share, token_share)

@external
@view
def get_info_at_index(index: uint256) -> (address, uint256):
	"""
     @dev Find out the address and shares at a particulat index
	 @return address, address of the shareholder
	 @return uint256, his/her relative shares in the pool
    """
	return (i_accounts[index], i_shares[index])


	
