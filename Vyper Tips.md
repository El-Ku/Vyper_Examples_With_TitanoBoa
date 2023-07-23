# What is this file about?

This file contains Vyper tips which I have come across. Some of them are available in the docs, but it wasn't obvious for me to notice. So I thought I will add them here, in case someone find it helpful.

I will be updating this file as often as I can.

### 1. Can I declare an `immutable` or `constant` variable as `public` too?

Yes. For example:
```python
owner: public(immutable(address))
```

### 2. How can I empty a dynamic array in Vyper?
```python
# array declaration
userList: DynArray[address, MAX_USER_LIST_SIZE]
# clears it.
self.userList = empty(DynArray[address, MAX_USER_LIST_SIZE])
```