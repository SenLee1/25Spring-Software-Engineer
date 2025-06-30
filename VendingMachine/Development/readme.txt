1. Setup the Environment 
python 3.10+
pip install pyzmq

2. Code Structure
/YourCodeExample/NetClient.py - This file is responsible for communicating with the server in the test cases.
/YourCodeExample/main.py - This file contains a sample student code, which you can modify to be the main file of your own designed system.
/TestCase/main.py - This file is responsible for sending test cases to your system and will interact based on the data sent by your system, including a very simple test case.
/TestCase/Server.py - This file is responsible for communicating with the client in the student code.

3.How to Run the Code
First, run /TestCase/main.py in Terminal to setup the judger.
Then, run /YourCodeExample/main.py in ANOTHER Terminal.
Finally, input 'y' to run the naive testcase.


4.available operation/event

    //available user operation
    insert_coin@money // E.g. insert_coin@0.5
    insert_bill@money // E.g. insert_bill
    select_product@index // E.g. select_product@1
    deselect_product@index // E.g. deselect_product@1
    purchase // E.g. purchase
    return_money // E.g. return_money
    log_in@password // E.g. log_in@123456

    //available admin operation
    log_out
    add_product@index // E.g. add_product@1
    add_coin@money  // E.g. add_coin@0.5
    remove_coin@money // E.g. remove_coin@0.5 
    add_bill@money //  E.g. add_bill@5  (1 belong to the coin)
    remove_bill@money // E.g. remove_bill@10


    //available system event
    coin_inserted@money
    bill_inserted@money
    product_selected@index
    product_deselected@index
    purchased@{index : num, index: num, ...}@{money : num,money:num, ...}
    money_returned@{money : num, money : num ,...}
    logged_in@password
    logged_out
    product_added@index
    coin_added@money
    coin_removed@money
    bill_added@money
    bill_removed@money
    
    "failed@" +  ["insert_coin@money","insert_bill@money","select_product@index","deselect_product@index",purchase,return_money
        log_in@password,log_out, add_product@index,add_coin@money,remove_coin@money,add_bill@money,remove_bill@money]


1. In the vending machine project,  user's operations are forbidden in the admin mode,admin's oerations are forbidden in the user mode
2. add_coin is valid for 0.5, 1 ,add_bill is valid for 5 , 10 , 20 , 50 , 100

initial state : 
    product     price       stock
       1          4           15
       2          3.5         20
       3          2           15
       4          5            1
       5          1            0
    password : 123456
    coin_box 
        0.5 : 5
        1   : 5
    bill_box 
        5   : 5
        10  : 5
        20  : 5
        50  : 5 
        100 : 5