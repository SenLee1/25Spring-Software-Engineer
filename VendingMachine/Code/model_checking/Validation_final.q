//This file was generated from (Academic) UPPAAL 5.1.0-beta5 (rev. C7C01B0740E14075), 2023-12-11

/*
1. The purpose of this quert is to ensure our system can execute without bugs.
*/
A[] not deadlock

/*
2. The purpose of this query is to ensure the wealth that the costumer has must remain the same as 
the money the customer has inserted (the customer will not lose money during using machine and will not gain additional money from the machine).
*/
A[] total_wealth_cur==current_money+price_goods_got && total_wealth_cur>=0

/*
3. The purpose of this query is to ensure the wealth that the machine has must remain the same as it has when the administrator use it last time(the machine will not lose and money and will not take money from customer but did not give products to the customer).
*/
A[] total_wealth_machine==total_money_machine+price_goods_machine-current_money && total_wealth_machine>=0

/*
4. The purpose of this query is to ensure that the customer will purchase successfully(gain product from machine and cost money) as long as the customer select products that has price less than the money that the customer has inserted.
*/
(Process1.Checking and Process3.Success) --> Process1.PurchaseSuccessfully

/*
5.The purpose of these query is to ensure that the customer can only add at most the number of product that the machine has.
*/
A[] c_chosen <= C
A[] b_chosen <= B
A[] a_chosen <= A
A[] d_chosen <= D
A[] e_chosen <= E

