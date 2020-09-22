import random
import socket
import time

#from _thread import all(*)
from _thread import *
import threading


from datetime import datetime
import json

#For data synchoronize
clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      #receive packet with size of 1024Bytes
      #and save packet in data, addr
      #[bits, [IP, PORT]] -> tuple, IP : sender of IP, PORT : sender of PORT
      data, addr = sock.recvfrom(1024)


      #send packet
      #can only send bytes datatype,  send "hello!" with 'utf8' format to addr[0](IP) and addr[1](PORT)
      #sock.sendto(bytes("Hello!",'utf8'), (addr[0], addr[1]))

      #convert data to string
      data = str(data)

      #check if addr(key) is in clients(dictionary)
      if addr in clients:
         #check if 'heartbeat' object(property) is in data
         #heartheat is used to check wheter client is still connected, client will sned hearthaed every second
         if 'heartbeat' in data:
            clients[addr]['lastBeat'] = datetime.now()

      #if it was new client
      else:
         if 'connect' in data:
            #2 = ALL_CLIENT_INFO
            allClientsInfo = {"cmd" : 2,
                              "numOfClients" : len(clients),
                              "allClients" : []}

            for c in clients:
               clientInfo = {}
               clientInfo["IP"] = c[0]
               clientInfo["PORT"] = c[1]
               allClientsInfo["allClients"].append(clientInfo)

            aci = json.dumps(allClientsInfo)
            #send all clients info to new client
            sock.sendto(bytes(aci,'utf8'), (addr[0], addr[1]))


            #make new pair
            clients[addr] = {}
            #populate info
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0

            #make message
            message = {"cmd" : 0,
                       "player" : {"id" : str(addr)}
                      }

            #convert python object(message) into json string
            m = json.dumps(message)

            #loop through all clinets(distionary) and get addr(key)
            #and using addr(key) send message
            for c in clients:
               #send m to c[0](IP), c[1](PORT)
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))

            idx = 0
            for player in clients:
               print("Player " + str(idx))
               print("IP: " + player[0])
               print("PORT: " + str(player[1]))
               idx += 1
               print("")

def cleanClients():
   while True:
      #loop all clinets
      for c in list(clients.keys()):
         #check time if lastbeat(client update this every second) has gone over 5second
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)

            #lock data
            clients_lock.acquire()

            del clients[c]

            #release data
            clients_lock.release()
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}

      #block
      clients_lock.acquire()
      #print (clients)
      for c in clients:
         player = {}
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      #print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      
      #relase the lock
      clients_lock.release()
      time.sleep(1)

def main():
   port = 12345

   #Create socket, type of UDP
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

   #bind new  socket to Local IP and port
   s.bind(('', port))

   #start thread
   #give funtion name and argument
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,())
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
