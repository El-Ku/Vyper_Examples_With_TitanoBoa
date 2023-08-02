# Testing Vyper Contracts With TitanoBoa

Being a relatively new language, Vyper at the moment has less docs available for us to refer to. And this can be frustrating. I have had my own share of frustration in this. So, here I have compiled some of the questions I had when I started Vyper programming and their answers. I hope you wouldnt have to struggle as much as I did on my journey. 

Thanks to the awesome [Vyper Discord community](https://discord.gg/HBCFTeqm), especially [@big_tech_sux](https://twitter.com/big_tech_sux) for the support.

I will be updating this file as often as I can.

# FAQ's:

### 1. My tests using Boa framework doesn't work as per its documentation.

The Boa interpreter is constantly evolving and might not be in sync with the latest version in github. Often there are updates to the repo which can be only accessed in the development version. So first thing you could try is to:
 1. Remove the current TitanBoa version with: `pip uninstall titanoboa`
 2. Reinstall Boa with: `pip install git+https://github.com/vyperlang/titanoboa`
- If it still doesn't work, write in the discord channel with a minimal reproducible code so that the experts can help

### 2. How can I pass a dynamic array to a constructor in my test?

You can do it just like you would any other variable. Create the array in python and pass it as an argument. 

```python
# Vyper function:
def create_pay_splitter(_accounts: DynArray[address, 100], _shares: DynArray[uint256, 100]):

# In python test file:
import random
accounts = []
shares = []
for i in range(5): # each array is of size 5
    accounts.append(boa.env.generate_address())
    s = random.randint(10,100)
    shares.append(s)

factory.create_pay_splitter(accounts, shares, value=10**18)  # set msg.value as 1 ether
```

### 3. How can I see the bytecode after deploying a contract?

```python
    # Deploy the source code as a blueprint and check its bytecode
    # Note the first 3 bytes will be the ERC-5202 preamble bytes which is `fe7100`, characteristic to a blueprint deployment.
    source = boa.load_partial("contracts/PaymentSplitter.vy") 
    blueprint = source.deploy_as_blueprint()
    print(blueprint.bytecode.hex())  #prints the bytecode in hex format

    # Deploy the source code and check its bytecode
    factory =  boa.load("PaymentSplitterFactory.vy")    
    print(factory.bytecode.hex())  #prints the bytecode in hex format
```

### 4. How can I see the emitted events in a transaction?

In your test file in python you can do it like this:
```python
# call directly from the contract object
with boa.env.prank(USER0):
    factory.create_pay_splitter(accounts, shares, value=10**18)
    print('\n', factory.get_logs())
##### OR, like this also you can call the function
with boa.env.prank(USER0):
    ret_call = boa.env.raw_call(to_address= factory.address, value = 10**18, data=data)
    print('\n', factory.get_logs(ret_call))
```

If there are two events logged, you can access them all from the same call to get_logs(). Example:
```python
    print('\n\n',factory.get_logs()[0])  # 1st event emitted in the transaction
    print('\n\n',factory.get_logs()[1])  # 2nd event emitted in the transaction
```

Note that `len(factory.get_logs())` will also return the number of events, which can be printed out in a `for` loop, if so desired.

### 5. How can I deploy a contract with `init` arguments? And how can I access the address of the deployed contract?

See the code from the [conftest file for FundMe project](https://github.com/El-Ku/Vyper_Examples_With_TitanoBoa/blob/c1d44fc567b2a90e6038715bf035fbd518a67444/all_contracts/FundMe/test/conftest.py#L13-L22)

As you can see, you can use fixtures to deploy contracts before the test begins. What is returned when we deploy using the `boa.load` method is a `VyperContract` object. The address of the contract can be accessed by `VyperContract.address`.

The `init` arguments can be passed to the contract after the file name, each argument separated by a comma.

### 7. How can I check for reverts?
Example:
```python
with boa.reverts("msg.value cannot be zero"):   # the next statement should revert with the given error message.
	fund_me.fund_contract()
```

For people coming from Solidity background, there are no custom errors in Vyper. 

### 8. How can I call a function with some `msg.value`?

Example:
```python
user = boa.env.generate_address("user")  # create an address
boa.env.set_balance(user, SEND_AMOUNT)  # give the new user some balance
with boa.env.prank(user):
    fund_me.fund_contract(value=SEND_AMOUNT)  # call the `fund_contract` function with `SEND_AMOUNT` ether.
```

Many more such examples can be found in [this](https://github.com/El-Ku/Vyper_Examples_With_TitanoBoa/blob/c1d44fc567b2a90e6038715bf035fbd518a67444/all_contracts/FundMe/test/test_fundme.py) test file.

### 9. How can I check for a revert, when a contract is sent just `ether` with no `data`?

You can use either `raw_call` or `execute_code` for this.

```python
import eth.exceptions  # make sure to import this for error handling when using `raw_call`

with boa.env.prank(USER0):
    with pytest.raises(eth.exceptions.Revert):  # makes sure that the raw_call got reverted
        # fund_me contract is sent some ether. which reverts as there is no __default__ method defined in it.
        boa.env.raw_call(fund_me.address, value = SEND_AMOUNT)  
```

The execute_code method doesn't revert on the above transaction. So we have to use a newly introduced method, `raw_call` as shown above.

Note that if `raw_call` isn't recognized, then update titanoboa to the latest dev version.

### 10. How can I call a function on an address?

For example, say we want to call a `transfer` function on an `ERC20` token contract. It can be done like this:
```python
boa.env.lookup_contract(erc20_contract_address).transfer(sender, receiver, amount)
```

### 11. How can I convert a contract address to a VyperContract object?

Suppose we have the contract already deployed at address `pay_splitter_addr`. We want to typecast it into a `VyperContract`.

```python
pay_splitter_deployer = boa.load_partial("contracts/PaymentSplitter.vy")
pay_splitter = pay_splitter_deployer.at(pay_splitter_addr)
# now you can use it to call functions in that address:
assert pay_splitter.get_total_shares() == total_shares
```

### 12. How can I prepare the data for passing it to a function?

An example:

```python
    function_signature = 'create_pay_splitter(address[],uint256[],address,uint256)'   
    # Encode the function parameters
    encoded_params = encode(['address[]', 'uint256[]', 'address', 'uint256'], [accounts, shares, _token, _amount])
    # Concatenate the function signature(first 4 bytes) and encoded parameters
    data = Web3.keccak(text=function_signature)[:4] + encoded_params
```

The accounts and shares are arrays and can be created, for example, in the following way:
```python
    import random
    _token = '0x0000000000000000000000000000000000001234'  # an address. 20 bytes. 
    for i in range(array_size):
        accounts.append(boa.env.generate_address())
        s = random.randint(10,100)
        shares.append(s)
```

### 13. How do I get the coverage report?

1. Install `coverage` in your venv with the following command:
```bash
python3 -m pip install coverage
```
2. Create a `.coveragerc` file in the project directory(in which you will run your pytest) and copy the following to it.
```
 [run] 
 plugins = boa.coverage 
```
3. Run the tests with the following command and then generate the report.
```bash
coverage run -m pytest
 # this will create a htmlcov folder in the project directory with coverage reports in html.
coverage html 
```

### 14. How can I test simple Vyper modules with Boa. Can I do it all(Python test+Vyper module) in one file?

Yes, For example, you can save the following in a `test.py` file and it will run fine:

```python
import boa
import pytest

contract = """
amount: public(uint256)

@external
def __init__(_amount: uint256):
    self.amount = _amount

@external
def set_amount(_amount: uint256):
	self.amount = _amount
"""

@pytest.fixture(scope="session")
def contract_deploy():
    return boa.loads(contract, 1000)

def test_contract(contract_deploy):
	assert contract_deploy.amount() == 1000
	contract_deploy.set_amount(100)
	assert contract_deploy.amount() == 100
```

### 15. How can I nicely printout the abi of a Vyper contract? 

You can use the standard Vyper command for this:
```bash
vyper -f abi contract.vy
```

But, this will print out the abi's all in one line. So if you want the abi's in multiple lines you can use `jq`. 

```bash
# Install jq if you dont have it already
sudo apt-get install jq 
# run the normal command and pass it to jq. 
vyper -f abi contract.vy | jq -c .[]
```

Thank you `Chanho` for the solution.

### 16. 


