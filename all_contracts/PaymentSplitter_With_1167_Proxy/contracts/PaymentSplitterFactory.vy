# @version 0.3.9
"""
@title PaymentSplitter Factory Contract in Vyper
@author ElKu
@license MIT
@notice Users can create a PaymentSplitter contract by using this contract
"""

from vyper.interfaces import ERC20

# External Interfaces
interface PaymentSplitter:
	def initialize(_owner: address, _accounts: DynArray[address, 100], _shares: DynArray[uint256, 100], _token: address, _amount: uint256, _total_shares: uint256): payable
	def total_shares() -> uint256: view

i_owner: public(immutable(address))
i_payment_splitter_impl: public(immutable(address))
protocol_fee: public(uint256)  # fixed fee
buffered_fee: public(uint256)
requested_fee_change_at: uint256
TIME_LOCK_FOR_BLOCKS: constant(uint256) = 10
nonces: HashMap[address, uint256]

# Events declarations
event FeeChanged:
    oldFee: uint256
    newFee: indexed(uint256)

event FeeChangeRequested:
	newFee : uint256

event SplitterContractCreated:
	owner: indexed(address)
	contract: indexed(address)
	accounts: DynArray[address, 100]
	shares: DynArray[uint256, 100]
	token: address
	amount: uint256
	value: uint256


@external
def __init__(_payment_splitter_impl: address, fee: uint256):
	"""
     @dev constructor function
     @param _payment_splitter_impl address The address of the Paymentsplitter implementation for which proxy is created
     @param fee uint256 The fixed protocol fee for contract creation. It can be zero.
    """
	i_owner = msg.sender
	self.protocol_fee = fee
	assert _payment_splitter_impl != empty(address), "Payment splitter address cannot be zero"
	i_payment_splitter_impl = _payment_splitter_impl

@external
@payable
def create_pay_splitter(_accounts: DynArray[address, 100], _shares: DynArray[uint256, 100], _token: address, _amount: uint256) -> address:
	"""
     @dev Creates a Paymentsplitter contract customized by the caller
     @param _accounts DynArray[address] The addresses which has a share in the contract funds
     @param _shares DynArray[uint256] The shares which decide what part of the funds can be withdrawn by a user
	 @param _token address The ERC20 token address 
	 @param _amount uint256 Amount of ERC20 tokens available to split among the _accounts
	 @return address The address of the contract created
    """	
	assert len(_accounts) == len(_shares), "accounts and shares length doesn't match"
	assert (_token != empty(address) and _amount > 0) or msg.value > self.protocol_fee, "At least payment must be an ERC20 token or ether"
	ts: uint256 = 0
	for s in _shares:
		assert s > 0, "No zero-value shares are allowed"
		ts += s
	# the ether or tokens present in the pool must be perfectly divisible by total_shares.
	value_to_be_send: uint256 = msg.value - self.protocol_fee
	if value_to_be_send > 0:
		assert (value_to_be_send/ts) * ts == value_to_be_send, "Splitter might leave dust ether"
	if _amount > 0:
		assert (_amount/ts) * ts == _amount, "Splitter might leave dust tokens"

	self.nonces[msg.sender] += 1  # increment nonce for unique addresses. salt starts from one.
	splitter: address = create_minimal_proxy_to(i_payment_splitter_impl, salt=convert(self.nonces[msg.sender], bytes32))
	assert splitter != empty(address), "Spliiter proxy is not created"
	# create the ERC 1167 proxy.
	PaymentSplitter(splitter).initialize(msg.sender, _accounts, _shares, _token, _amount, ts, value=value_to_be_send)
	# Initialize the state variables stored in the proxy. The logic is implemented at the i_payment_splitter_impl address.
	if(_token != empty(address) and _amount > 0):  #transfer tokens from user to newly created contract if its necessary
		assert ERC20(_token).transferFrom(msg.sender, splitter, _amount) == True
	log SplitterContractCreated(msg.sender, splitter, _accounts, _shares, _token, _amount, msg.value)  # Event 
	return splitter

@external 
def request_to_set_protocol_fee(fee: uint256):
	"""
     @dev Allows owner to request to change the protocol fee
     @param fee uint256 The new protocol fee
	"""
	assert msg.sender == i_owner, "only owner can request a fee change"
	self.buffered_fee = fee
	self.requested_fee_change_at = block.number
	log FeeChangeRequested(fee)

@external 
def set_protocol_fee():
	"""
     @dev Allows anyone to confirm the fee change as long as the lock period is over
	"""
	assert self.requested_fee_change_at + TIME_LOCK_FOR_BLOCKS <= block.number, "time lock period to change fee is not yet over"
	log FeeChanged(self.protocol_fee, self.buffered_fee)
	self.protocol_fee = self.buffered_fee
	
@external
@view
def get_nonces(user: address) -> uint256:
	"""
     @dev Get the current nonce of an address
	 @param user address User address
	 @return uint256 Current nonce of the user
	"""
	return self.nonces[user]