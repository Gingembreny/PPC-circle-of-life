import sysv_ipc
 
key = 128
 
mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)

user_input = "EVENT"
while user_input:
    message = ""
    try:
        user_input = input()
        command = user_input.split() # 0: command type; 1: event type 2: argument of event

        if command[0] == "EVENT":
            print("OK")
            message = "EVENT " + command[1] + " " + command[2]
            
            
        else:
            raise Exception("Unrecognized command. Only commands available are: EVENT")
    except:
        print("ERROR:")
        print("Commands should be typed as 'EVENT type args'")
    else:
        if message != "":
            message = str(user_input).encode()
            mq.send(message)
            print("MESSAGE SENT")
    
 
mq.remove()