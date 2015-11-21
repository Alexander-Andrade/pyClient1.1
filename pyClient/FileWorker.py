﻿from SocketWrapper import SocketWrapper
import os
import io
import sys
class FileWorkerError(Exception):
    #
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class FileWorker:
    

    def __init__(self,sockWrapper,recoveryFunc,bufferSize,timeOut):
        self.timeOut = timeOut
        self.bufferSize = bufferSize
        self.sock = sockWrapper
        self.fileLen = 0
        self.file = None
        self.filePos = 0
        self.loadingPercent = 0
        #UDP packet controll
        self.datagramsId = []
        #number of udp datagrams answer send afrer
        self.nUdpPacksCtrl = 1
        self.recoveryFunc = recoveryFunc


    def outFileInfo(self):
        #print file name
        print("filename:",end='')
        print(self.fileName)
        #file size
        print("file size:",end='')
        print(self.fileLen,flush=True)


    def send(self,fileName):
        self.fileName = fileName
        if not os.path.exists(fileName):
            raise FileWorkerError("file does not exist") 
        try:
            #binary mode
            self.file = open(fileName,'rb')
        except OSError:
            #say to receiver that can't open the file
            self.sock.sendRefuse()
            raise FileWorkerError("can't open the file")
        self.sock.sendConfirm()

        self.sock.setSendBufferSize(self.bufferSize)
        #real system buffer size can differ
        self.bufferSize = self.sock.getSendBufferSize()
        #file size in bytes
        self.fileLen = os.path.getsize(fileName)
        #send hint configs to the receiver
        try:
            self.sock.sendNum(self.bufferSize)
            self.sock.sendNum(self.timeOut)
            self.sock.sendNum(self.fileLen)
        except OSError:
            raise FileWorkerError("can't send file metadata")
        self.outFileInfo
        #file transfer
        try:
            while True:
                data = self.file.read(self.bufferSize)

                #if eof
                if not data:
                    self.sock.raw_sock.settimeout(self.timeOut)
                    #receiver acknowledge received data size
                    receiverPos = self.sock.recvNum()
                    if receiverPos == self.filePos:
                        break
                    else:
                        raise OSError("fail to transfer file")

                #send data portion
                #error will rase OSError    
                self.sock.raw_sock(data)
                self.filePos += len(data)
        except OSError as e:
            #file transfer reconnection
            print(e.args[0])
        finally:
            self.file.close() 
            

    def receive(self,fileName):
        self.fileName = fileName
        #waiting for checking file existance from transiving side
        if not self.sock.recvAck():
            raise FileWorkerError("there is no such file")
        try:
            self.file.open(fileName,"wb")
        except OSError:
            raise FileWorkerError("can't create the file")
        #get hints configs from the transmitter
        try:
            self.bufferSize = self.sock.recvNum()
            self.timeOut = self.sock.recvNum()
            self.fileLen = self.sock.recvNum()
        except OSError:
            raise FileWorkerError("can't receive file metadata")
        #set timeout on receive op,to avoid program freezing
        self.sock.setReceiveTimeout(self.timeOut)
        self.outFileInfo()
        #file writing cycle
        try:
            while True:
                data = self.sock.raw_sock.recv(self.bufferSize)
                self.file.write(data)
                self.filePos += len(data)

                if self.filePos == self.fileLen:
                    #send ack to end the file transmittion
                    sefl.sock.sendNum(self.filePos)
                    break
        except OSError as msg:
             #file transfer reconnection
            print(e.args[0])
        finally:
            self.sock.disableReceiveTimeout()
            self.file.close()



