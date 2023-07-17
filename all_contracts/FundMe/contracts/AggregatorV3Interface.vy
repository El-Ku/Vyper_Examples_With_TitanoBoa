# @version 0.3.9

@external 
@pure
def decimals() -> uint8:
	return 8

@external
@pure
def latestRoundData() -> (uint80, int256, uint256, uint256, uint80):  
	# for the sake of this test, lets fix it as 2000 usd for 1 eth
	return 0 , (2000 * 10**8), 0, 0, 0