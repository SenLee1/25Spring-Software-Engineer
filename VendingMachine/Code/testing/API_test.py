import NetClient
import time
import threading
#Feel free to rewrite this file!
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../system")))
from UI import UserInterface
from VM import VendingMachine
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from UIbridge import UIFeedbackBridge

# This function determines whether a new message has been received
def is_received_new_message(oldTimeStamp:int, oldServerMessage:str, Msgunprocessed:bool = False)->bool:
    if(Msgunprocessed):
        return True
    else:
        if(oldTimeStamp == zmqThread.messageTimeStamp and 
           oldServerMessage == zmqThread.receivedMessage):
            return False
        else:
            return True

def message_processing_loop():
    ############ Initialize Banking System ############
    timeStamp = -1 #Used when receiving new message
    serverMessage = "" #Used when receiving new message
    
    while(True):
        ############ Your Banking system design ############
        ##Example just for the naive testcase
        if(is_received_new_message(timeStamp,serverMessage)):
            timeStamp = zmqThread.messageTimeStamp
            serverMessage = zmqThread.receivedMessage

            
            if serverMessage.startswith("log_in"):
                password = serverMessage.split("@")[1]
                if vm.verify_admin(password):
                    ui_bridge.update_ui(lambda: ui.login_succeeded())
                    zmqThread.sendMsg("logged_in@" + password)
                else:
                    ui_bridge.update_ui(lambda: ui.login_failed(password))
                    zmqThread.sendMsg("failed@log_in@" + password)

            elif serverMessage.startswith("add_product"):
                index = serverMessage.split("@")[1]
                if ui.state and vm.restock_product(int(index) - 1):
                    ui_bridge.update_ui(lambda: ui.add_product_succeeded())
                    zmqThread.sendMsg("product_added@" + index)
                else:
                    ui_bridge.update_ui(lambda: ui.admin_failed())
                    zmqThread.sendMsg("failed@product_add@" + index)

            elif serverMessage.startswith("add_coin"):
                coin = serverMessage.split("@")[1]
                if ui.state and vm.refill_coin(float(coin)):
                    ui_bridge.update_ui(lambda: ui.add_coin_succeeded())
                    zmqThread.sendMsg("coin_added@" + coin)
                else:
                    ui_bridge.update_ui(lambda: ui.admin_failed())
                    zmqThread.sendMsg("failed@coin_add@" + coin)

            elif serverMessage.startswith("add_bill"):
                money = serverMessage.split("@")[1]
                if ui.state and vm.refill_coin(int(money)):
                    ui_bridge.update_ui(lambda: ui.add_bill_succeeded())
                    zmqThread.sendMsg("bill_added@" + money)
                else:
                    ui_bridge.update_ui(lambda: ui.admin_failed())
                    zmqThread.sendMsg("failed@bill_add@" + money)

            elif serverMessage.startswith("remove_coin"):
                coin = serverMessage.split("@")[1]
                if ui.state and vm.withdraw_coin(float(coin)):
                    ui_bridge.update_ui(lambda: ui.remove_money_succeeded())
                    zmqThread.sendMsg("coin_removed@" + coin)
                else:
                    ui_bridge.update_ui(lambda: ui.admin_failed())
                    zmqThread.sendMsg("failed@coin_remove@" + coin)

            elif serverMessage.startswith("remove_bill"):
                bill = serverMessage.split("@")[1]
                if ui.state and vm.withdraw_coin(int(bill)):
                    ui_bridge.update_ui(lambda: ui.remove_money_succeeded())
                    zmqThread.sendMsg("bill_removed@" + bill)
                else:
                    ui_bridge.update_ui(lambda: ui.admin_failed())
                    zmqThread.sendMsg("failed@bill_remove@" + bill)

            elif serverMessage.startswith("log_out"):
                if ui.state:
                    ui_bridge.update_ui(lambda: ui.logout_succeeded())
                    zmqThread.sendMsg("logged_out")
                else:
                    zmqThread.sendMsg("failed@log_out")

            elif serverMessage.startswith("insert_coin"):
                coin = serverMessage.split("@")[1]
                if not ui.state:
                    vm.insert_coin(float(coin))
                    ui_bridge.update_ui(lambda: ui.insert_money())
                    zmqThread.sendMsg("coin_inserted@" + coin)
                else:
                    ui_bridge.update_ui(lambda: ui.user_failed())
                    zmqThread.sendMsg("failed@coin_insert@" + coin)

            elif serverMessage.startswith("insert_bill"):
                bill = serverMessage.split("@")[1]
                if not ui.state:
                    vm.insert_coin(int(bill))
                    ui_bridge.update_ui(lambda: ui.insert_money())
                    zmqThread.sendMsg("bill_inserted@" + bill)
                else:
                    ui_bridge.update_ui(lambda: ui.user_failed())
                    zmqThread.sendMsg("failed@bill_insert@" + bill)

            elif (serverMessage.startswith("return_money")):
                # in this test, the returned money is {5 : 1}
                if not ui.state:
                    success, returned_money, msg = vm.refund_all()
                    ui_bridge.update_ui(lambda: ui.return_money(msg))
                    if success:
                        zmqThread.sendMsg("money_returned@" + str(returned_money))
                    else:
                        zmqThread.sendMsg("failed@return_money")
                else:
                    ui_bridge.update_ui(lambda: ui.user_failed())
                    zmqThread.sendMsg("failed@return_money")

            elif serverMessage.startswith("select_product"):
                index = serverMessage.split("@")[1]
                if not ui.state and vm.add_to_cart(int(index) -  1):
                    ui_bridge.update_ui(lambda: ui.select_product_succeeded())
                    zmqThread.sendMsg("product_selected@" + index)
                else:
                    ui_bridge.update_ui(lambda: ui.select_product_failed())
                    zmqThread.sendMsg("failed@product_select@" + index)

            elif serverMessage.startswith("deselect_product"):
                index = serverMessage.split("@")[1]
                if not ui.state and vm.remove_from_cart(int(index) - 1):
                    ui_bridge.update_ui(lambda: ui.deselect_product_succeeded())
                    zmqThread.sendMsg("product_deselected@" + index)
                else:
                    ui_bridge.update_ui(lambda: ui.deselect_product_failed())
                    zmqThread.sendMsg("failed@product_deselect@" + index)

            elif (serverMessage.startswith("purchase")):
                #  in this test, products_selected = {2 : 1}
                if not ui.state:
                    success, products_selected, msg = vm.process_payment()
                    if success:
                        _, change_strategy, return_msg = vm.refund_all()
                    ui_bridge.update_ui(lambda: ui.purchase(msg))
                    if success:
                        ui_bridge.update_ui(lambda: ui.return_money(return_msg))
                        zmqThread.sendMsg("purchased@" + str(products_selected) + "@" + str(change_strategy))
                    else:
                        zmqThread.sendMsg("failed@purchase" + "@" + msg)
                else:
                    ui_bridge.update_ui(lambda: ui.user_failed())
                    zmqThread.sendMsg("failed@purchase")
                # use your algorithm to select a change-making strategy,in this test , the strategy {0.5 : 1,1 : 2,5 : 1} is suitable

    
        time.sleep(0.01)

        

if __name__=='__main__':
    global vm, app, ui_bridge
    ############ Connect the Server ############
    app = QApplication(sys.argv)
    vm = VendingMachine()

    identity = "Team08" #write your team name here.
    zmqThread = NetClient.ZmqClientThread(identity=identity)

    ui = UserInterface(vm, zmqThread)
    ui.show()
    
    ui_bridge = UIFeedbackBridge(ui)
    message_thread = threading.Thread(target=message_processing_loop, daemon=True)
    message_thread.start()
    
    sys.exit(app.exec_())        

    '''
    For Other kinds of available serverMessage, see readMe.txt
    '''
    
