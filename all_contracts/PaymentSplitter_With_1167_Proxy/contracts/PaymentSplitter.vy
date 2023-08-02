# @version 0.3.9
"""
@title PaymentSplitter Contract in Vyper
@author ElKu
@license MIT
@notice This contract is deployed by the factory contract by users who wants to split some ether or ERC20 tokens among a set of addresses
"""

from vyper.interfaces import ERC20

initialized: bool
TIME_LOCK_DURATION: constant(uint256) = 7*24*60*60  # one week
owner: public(address)
created_at: public(uint256)
accounts: DynArray[address, 100]
shares: DynArray[uint256, 100]
total_eth_to_split: public(uint256)
total_tokens_to_split: public(uint256)
token: public(address)
total_shares: public(uint256)
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
def initialize(_owner: address, _accounts: DynArray[address, 100], _shares: DynArray[uint256, 100], _token: address, _amount: uint256, _total_shares: uint256):
	"""
     @dev Initializes the contract right after the ERC 1167 proxy is created
     @param _owner address The address which created and funded this contract
     @param _accounts DynArray[address] The addresses which has a share in the contract funds
     @param _shares DynArray[uint256] The shares which decide what part of the funds can be withdrawn by a user
	 @param _token address The ERC20 token address 
	 @param _amount uint256 Amount of ERC20 tokens available to split among the _accounts
    """
	assert self.initialized == False, "Can be initialized only once"
	self.initialized = True
	self.token = _token
	self.owner = _owner
	self.created_at = block.timestamp   # contract creation time
	self.accounts = _accounts
	self.shares = _shares
	self.total_eth_to_split = msg.value
	self.total_tokens_to_split = _amount
	self.total_shares = _total_shares  #sum of all shares

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
	for account in self.accounts:
		if msg.sender == account:
			acc_share = self.shares[i]
			self.paid_accounts[msg.sender] = True
			break
		i += 1
	eth: uint256 = 0
	tokens: uint256 = 0
	if self.total_eth_to_split > 0:
		eth = self.total_eth_to_split*acc_share/self.total_shares
		send(msg.sender, eth)  # send ether if its more than zero.
	if self.total_tokens_to_split > 0:
		tokens = self.total_tokens_to_split*acc_share/self.total_shares
		assert ERC20(self.token).transfer(msg.sender, tokens) == True # send erc20 tokens if its more than zero.
	log SharesPaid(msg.sender, eth, tokens)  # Event
	return True

@external
def withdraw() -> bool:
	"""
     @dev Used by account's owner to withdraw back funds which are in the contract which hasnt been taken even after the TIME_LOCK_DURATION
	 @return bool, True if funds were successfully sent back to the owner
    """
	assert self.owner == msg.sender, "Only owner can withdraw"
	assert block.timestamp >= self.created_at + TIME_LOCK_DURATION, "Too early to withdraw funds"
	log FundsWithdrawn(self.balance, ERC20(self.token).balanceOf(self))   # Event 
	if(self.balance > 0):
		send(self.owner, self.balance)
	if(ERC20(self.token).balanceOf(self) > 0):
		assert ERC20(self.token).transfer(self.owner, ERC20(self.token).balanceOf(self)) == True
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
	for account in self.accounts:
		if acc == account:
			acc_share = self.shares[i]
			break
		i += 1
	eth_share: uint256 = self.total_eth_to_split*acc_share/self.total_shares
	token_share: uint256 = self.total_tokens_to_split*acc_share/self.total_shares
	return (eth_share, token_share)

@external
@view
def get_info_at_index(index: uint256) -> (address, uint256):
	"""
     @dev Find out the address and shares at a particulat index
	 @return address, address of the shareholder
	 @return uint256, his/her relative shares in the pool
    """
	return (self.accounts[index], self.shares[index])
