# @version 0.3.9
"""
@title SimpleStorage Contract in Vyper
@author ElKu
@license MIT
@notice Just the very first contract in Vyper I made. To store and retrieve a number
"""
val: public(uint256)

@external 
def __init__(_val: uint256):
    self.val = _val

@external
def store(_val: uint256):
    self.val = _val

@external
def get() -> uint256:
    return self.val