import sys
import os
import ast
import Server
import time
import random
from enum import IntEnum
import queue
#######   BANKING PROJECT    #######

### Simple Test Case ###
def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            contents = [line.strip() for line in file]
        return contents
    except FileNotFoundError:
        print(f"Error: file '{file_path}' is not found!")
        return []
    except Exception as e:
        print(f"Error reading file: {e}!")
        return []

test_file = f"./testcase/testcase.txt"
answer_file = f"./answer/answer.txt"
def testing(server:Server.ZmqServerThread):
    def is_received_new_message(oldTimeStamp:int, oldServerMessage:str, Msgunprocessed:bool = False)->bool:
        if(Msgunprocessed):
            return True
        else:
            if(oldTimeStamp == server.messageTimeStamp and 
            oldServerMessage == server.receivedMessage):
                return False
            else:
                return True

    send_list = read_file(test_file)
    answer_list = read_file(answer_file)

    ############ Initialize Customers ############
    timeStamp = -1 #default time stamp is -1
    clientMessage = "" #default received message is ""

    send_count = 0
    answer_count = 0
    correct_count = 0

    server.send_string(server.bindedClient, send_list[send_count])
    send_count += 1

    finish = False
    ############ Customer timed automata ############
    while(True):
        if(is_received_new_message(timeStamp,clientMessage)):
            timeStamp = server.messageTimeStamp
            clientMessage = server.receivedMessage


            if (not clientMessage.startswith("Client")):
                if clientMessage == answer_list[answer_count]:
                    answer_count += 1
                    if answer_count == len(answer_list):
                        result = "PASSED!"
                        server.send_string(server.bindedClient, result)
                        break
                    server.send_string(server.bindedClient,send_list[send_count])
                    send_count += 1
                else:
                    result = "FAILED!"
                    server.send_string(server.bindedClient, result)
                    break

        time.sleep(0.01)


if __name__ == "__main__":
    my_server = Server.ZmqServerThread()
    while(True):
        if(len(my_server.clients_addr) == 0):
            continue
        elif(len(my_server.clients_addr) >=2 ):
            print('more than 1 client address stored. server will exit')
            sys.exit()
        else:
            addr = list(my_server.clients_addr)[0]
            msg = input(f"Initiate evaluation for {addr}?: (y/n)\n")
            if msg == 'y':
                my_server.bindedClient = addr
                testing(my_server)
                break
            else:
                continue