# Approvals Detection

## Mission

1. Explain in your own words what is an approval, and what are the differences between a transfer to a transferFrom function.

    * Approval is an event that is logged when a successful approve call was made - the approve function gives another address (e.g. some ICO contract) authorization to transfer from the issuer of the approve function up to a given amount. If I want to give a specific ICO contract e.g. myICO, permission to sell my coin up to e.g. 10000 units, then I will make an approve call on my coin with myICO and 10000 as the parameters of the approve.  
    Then, myICO could use the function transferFrom(myAddress, someAddress, x) however much times it wants, as long as x is less or equal to the remaining approval value I stated above (if spent already 1000 units, it can only spend another 9000 units from now on...).  

    * The difference between a transfer and a transferFrom function, is that the transfer is used to transfer funds to a specific address, from my address, and is issued by me, while the transferFrom function is issued by some approved address to transfer funds from my account to a specific address. Again, the transferFrom function needs to be approved by my address before being issued by the approved address.

2. Write a simple **python script** that gets a public address on the blockchain and gets all the approvals it ever approved  
   The script should run as follows:  
   ```bash
   $ python my_approvals.py --address 0x...
   approval on US Tether on amount of 13
   approval on UnknownERC20 on amount of 1 
   approval on USDT on amount of 77
   ...
   ```