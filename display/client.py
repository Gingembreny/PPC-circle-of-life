import sysv_ipc
 
key = 128
 
mq = sysv_ipc.MessageQueue(key)
 
while True:
    message, t = mq.receive()
    received = message.decode()
    if received:
        print("received:", received)
        
    else:
        print("exiting.")
        break