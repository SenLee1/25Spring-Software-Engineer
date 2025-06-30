//This file was generated from (Academic) UPPAAL 5.0.0 (rev. 714BA9DB36F49691), 2023-06-21

/*

*/
A[] elevator_floor[1] <= 3 && elevator_floor[1] >= -1

/*

*/
A[] elevator_floor[0] <= 3 && elevator_floor[0] >= -1

/*

*/
A[] passenger2_state <= 2 && passenger2_state >= 0

/*

*/
A[] passenger1_state <= 2 && passenger1_state >= 0

/*

*/
A[] elevator_state[1] != 0 imply door2.Closed

/*

*/
A[] elevator_state[0] != 0 imply door1.Closed

/*

*/
A[] (door2.Open || door2.Openning || door2.Closing) imply elevator_state[1] == 0

/*

*/
A[] (door1.Open || door1.Openning || door1.Closing) imply elevator_state[0] == 0

/*

*/
A[] (elevator_state[1] == 0) imply (elevator2.Floor_minus1 || elevator2.Floor_1 || elevator2.Floor_2 || elevator2.Floor_3 || elevator2.Check_arrived || elevator2.Signal1 || elevator2.Signal2 || elevator2.Signal3 || elevator2.Signal4)

/*

*/
A[] (elevator_state[0] == 0) imply (elevator1.Floor_minus1 || elevator1.Floor_1 || elevator1.Floor_2 || elevator1.Floor_3 || elevator1.Check_arrived || elevator1.Signal1 || elevator1.Signal2 || elevator1.Signal3 || elevator1.Signal4)

/*

*/
E<> passenger_done[1]

/*

*/
E<> passenger_done[0]

/*

*/
E<> door2.Open

/*

*/
E<> door1.Open

/*

*/
A[] not deadlock
