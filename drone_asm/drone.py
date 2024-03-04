# File: drone.py
# Author: Michael Huelsman
# Copyright: Dr. Michael Andrew Huelsman 2024
# License: GNU GPLv3
# Created On: 03 Mar 2024
# Purpose:
#   A class for interacting with a Tello drone.
# Notes:
import os
from threading import Thread
from socket import socket, AF_INET, SOCK_DGRAM
from time import perf_counter, sleep
import cv2 as cv
from datetime import datetime
from abc import ABC, abstractmethod
from math import sin, cos, radians
import numpy as np


# Abstract base class for drones.
class Drone(ABC):
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def shutdown(self):
        pass
    
    @abstractmethod
    def takeoff(self):
        pass
    
    @abstractmethod
    def land(self):
        pass
    
    @abstractmethod
    def forward(self, val):
        pass
    
    @abstractmethod
    def backward(self, val):
        pass
    
    @abstractmethod
    def left(self, val):
        pass
    
    @abstractmethod
    def right(self, val):
        pass
    
    @abstractmethod
    def up(self, val):
        pass
    
    @abstractmethod
    def down(self, val):
        pass
    
    @abstractmethod
    def rotate_cw(self, val):
        pass
    
    @abstractmethod
    def rotate_ccw(self, val):
        pass
    
    @abstractmethod
    def get_frame(self):
        pass
    
    @abstractmethod
    def get_state(self):
        pass


class TelloDrone(Drone):
    # Precond:
    #   None.
    #
    # Postcond:
    #   Sets up the required steps for controlling a Tello drone.
    def __init__(self, log_fldr="logs/"):
        # Addresses
        self.tello_addr = '192.168.10.1'
        self.cmd_port = 8889
        self.state_port = 8890
        self.video_port = 11111
        
        # Setup channels
        self.send_channel = socket(AF_INET, SOCK_DGRAM)
        self.send_channel.bind(('', self.cmd_port))
        
        self.state_channel = socket(AF_INET, SOCK_DGRAM)
        self.state_channel.bind(('', self.state_port))
        
        # Video setup
        self.video_connect_str = 'udp://' + self.tello_addr + ":" + str(self.video_port)
        self.video_stream = None
        self.video_thread = Thread(target=self.__receive_video)
        self.video_thread.daemon = True
        self.last_frame = None
        self.stream_active = False
        self.frame_width = 0
        self.frame_height = 0
        
        # Basic accounting variables
        self.flying = False
        self.active = False
        self.connected = False
        self.rc_freq = 30
        self.cmd_log = []
        self.last_state = None
        self.MAX_TIMEOUT = 5
        
        # Threads
        self.receive_thread = Thread(target=self.__receive)
        self.receive_thread.daemon = True
        self.state_thread = Thread(target=self.__receive_state)
        self.state_thread.daemon = True
        
        # Setup log directory
        self.log_fldr = log_fldr
        if not os.path.exists(self.log_fldr):
            os.mkdir(self.log_fldr)
    
    # Precond:
    #   None.
    #
    # Postcond:
    #   Attempts (up to 5 times) to connect to the Tello drone and start all needed threads.
    #   Returns True if connection was made.
    def connect(self):
        self.active = True
        # Starting needed threads
        self.receive_thread.start()
        if not self.__connect():
            print("Problem connecting to drone.")
            return False
        self.video_start()
        self.state_thread.start()
        return True
    
    # Precond:
    #   None.
    #
    # Postcond:
    #   Starts the state receiving thread.
    def video_start(self):
        # Set up the video stream
        self.stream_active = True
        self.video_stream = cv.VideoCapture(self.video_connect_str, cv.CAP_ANY)
        self.frame_width = self.video_stream.get(cv.CAP_PROP_FRAME_WIDTH)
        self.frame_height = self.video_stream.get(cv.CAP_PROP_FRAME_HEIGHT)
        self.video_thread.start()
    
    # Precond:
    #   None.
    #
    # Postcond:
    #   Returns the last grabbed video frame.
    def get_frame(self):
        return self.last_frame
    
    # Precond:
    #   None.
    #
    # Postcond:
    #   Returns the last received state as a dictionary.
    def get_state(self):
        return self.last_state
    
    # Precond:
    #   None.
    #
    # Postcond:
    #   Stops the connection and lands (if needed) the drone.
    def shutdown(self):
        if self.connected:
            if self.flying:
                self.__send_cmd("land")
            self.active = False
            self.stream_active = False
            self.send_channel.close()
            self.last_frame = None
            sleep(1)
            self.receive_thread.join()
            self.video_thread.join()
        t = datetime.now()
        log_name = os.path.join(self.log_fldr, t.strftime("%Y-%m-%d_%H-%M-%S") + '-cmd.log')
        with open(log_name, 'w') as fout:
            count = 0
            for entry in self.cmd_log:
                print("Message[" + str(count) + "]:", entry[0], file=fout)
                print("Response[" + str(count) + "]:", entry[1], file=fout)
                count += 1
    
    # ======================================
    # COMMAND METHODS
    # ======================================
    
    # Precond:
    #   None.
    #
    # Postcond
    #   Sends the takeoff command to the drone
    def takeoff(self) -> bool:
        res = self.__send_cmd("takeoff")
        return res is not None and res == "ok"
    
    # Precond:
    #   None.
    #
    # Postcond
    #   Sends the land command to the drone.
    def land(self) -> bool:
        res = self.__send_cmd("land")
        return res is not None and res == "ok"
    
    # Precond:
    #   val is an integer representing the amount to move
    #
    # Postcond:
    #   Sends the up command to the drone.
    def up(self, val) -> bool:
        if val not in range(20, 501):
            return False
        res = self.__send_cmd("up " + str(val))
        return res is not None and res == "ok"
    
    # Precond:
    #   val is an integer representing the amount to move
    #
    # Postcond:
    #   Sends the down command to the drone.
    def down(self, val) -> bool:
        if val not in range(20, 501):
            return False
        res = self.__send_cmd("down " + str(val))
        return res is not None and res == "ok"
    
    # Precond:
    #   val is an integer representing the amount to move
    #
    # Postcond:
    #   Sends the left command to the drone.
    def left(self, val) -> bool:
        if val not in range(20, 501):
            return False
        res = self.__send_cmd("left " + str(val))
        return res is not None and res == "ok"
    
    # Precond:
    #   val is an integer representing the amount to move
    #
    # Postcond:
    #   Sends the right command to the drone.
    def right(self, val) -> bool:
        if val not in range(20, 501):
            return False
        res = self.__send_cmd("right " + str(val))
        return res is not None and res == "ok"
    
    # Precond:
    #   val is an integer representing the amount to move
    #
    # Postcond:
    #   Sends the forward command to the drone.
    def forward(self, val) -> bool:
        if val not in range(20, 501):
            return False
        res = self.__send_cmd("forward " + str(val))
        return res is not None and res == "ok"
    
    # Precond:
    #   val is an integer representing the amount to move
    #
    # Postcond:
    #   Sends the backward command to the drone.
    def backward(self, val) -> bool:
        if val not in range(20, 501):
            return False
        res = self.__send_cmd("backward " + str(val))
        return res is not None and res == "ok"
    
    # Precond:
    #   val is an integer representing the amount to move
    #
    # Postcond:
    #   Sends the rotate cw command to the drone.
    def rotate_cw(self, val) -> bool:
        if val not in range(1, 361):
            return False
        res = self.__send_cmd("rotate cw " + str(val))
        return res is not None and res == "ok"
    
    # Precond:
    #   val is an integer representing the amount to move
    #
    # Postcond:
    #   Sends the rotate ccw command to the drone.
    def rotate_ccw(self, val) -> bool:
        if val not in range(1, 361):
            return False
        res = self.__send_cmd("rotate ccw " + str(val))
        return res is not None and res == "ok"
    
    # Precond:
    #   attempts is the number of times to try and connect.
    #
    # Postcond:
    #   Checks connection to the drone by sending a message to
    #     switch the drone into SDK mode.
    #   Returns true if the connection was made.
    #   Returns false if there was a problem connecting and attempts were
    #       exceeded.
    def __connect(self, attempts=5):
        for _ in range(attempts):
            res = self.__send_cmd("command")
            if res is not None and res == 'ok':
                self.connected = True
                self.__send_cmd("streamon")
                return True
        return False
    
    # Precond:
    #   msg is a string containing the message to send.
    #
    # Postcond:
    #   Sends the given message to the Tello.
    #   Returns the response string if the message was received.
    #   Returns None if the message failed.
    def __send_cmd(self, msg: str) -> str | None:
        self.cmd_log.append([msg, None])
        self.send_channel.sendto(msg.encode('utf-8'), (self.tello_addr, self.cmd_port))
        # Response wait loop
        start = perf_counter()
        while self.cmd_log[-1][1] is None:
            if (perf_counter() - start) > self.MAX_TIMEOUT:
                self.cmd_log[-1][1] = "TIMED OUT"
                return None
        return self.cmd_log[-1][1]
    
    # Precond:
    #   msg is a string containing the message to send.
    #
    # Postcond:
    #   Sends the given message to the Tello.
    #   Does not wait for a response.
    #   Used (internally) only for sending the emergency signal or rc values.
    def __send_nowait(self, msg):
        self.send_channel.sendto(msg.encode('utf-8'), (self.tello_addr, self.cmd_port))
        return None
    
    # Precond:
    #   None.
    #
    # Postcond:
    #   Receives messages from the Tello and logs them.
    def __receive(self):
        while self.active:
            try:
                response, ip = self.send_channel.recvfrom(1024)
                response = response.decode('utf-8')
                self.cmd_log[-1][1] = response.strip()
            except OSError as exc:
                if self.active:
                    print("Caught exception socket.error : %s" % exc)
            except UnicodeDecodeError as _:
                if self.active:
                    self.cmd_log[-1][1] = "Decode Error"
                    print("Caught exception Unicode 0xcc error.")
    
    # Precond:
    #   None.
    #
    # Postcond:
    #   Receives video messages from the Tello.
    def __receive_video(self):
        while self.stream_active:
            ret, img = self.video_stream.read()
            if ret:
                self.last_frame = img
        self.video_stream.release()
    
    # Precond:
    #   None.
    #
    # Postcond:
    #   Receives state information from the Tello and logs it.
    def __receive_state(self):
        while self.active:
            try:
                response, ip = self.state_channel.recvfrom(1024)
                response = response.decode('utf-8')
                response = response.strip()
                vals = response.split(';')
                state = {}
                for item in vals:
                    if item == '':
                        continue
                    label, val = item.split(':')
                    state[label] = val
                self.last_state = state
            except OSError as exc:
                if self.active:
                    print("Caught exception socket.error : %s" % exc)
            except UnicodeDecodeError as _:
                if self.active:
                    self.cmd_log[-1][1] = "Decode Error"
                    print("Caught exception Unicode 0xcc error.")


class SimulatedDrone(Drone):
    def __init__(self):
        self.location = [0, 0, 0]
        self.facing = 0.0
        self.connected = True
        self.flying = False
    
    def connect(self):
        self.connected = True
        return True
    
    def shutdown(self):
        self.connected = False
    
    def takeoff(self):
        self.flying = True
        return True
    
    def land(self):
        self.flying = False
        return True
    
    def forward(self, val):
        self.location[0] += val * cos(self.facing)
        self.location[1] += val * sin(self.facing)
        return True
    
    def backward(self, val):
        self.location[0] -= val * cos(self.facing)
        self.location[1] -= val * sin(self.facing)
        return True
    
    def left(self, val):
        self.location[0] += val * cos(self.facing + radians(90))
        self.location[1] += val * sin(self.facing + radians(90))
        return True
    
    def right(self, val):
        self.location[0] += val * cos(self.facing - radians(90))
        self.location[1] += val * sin(self.facing - radians(90))
        return True
    
    def up(self, val):
        self.location[2] += val
        return True
    
    def down(self, val):
        self.location[2] -= val
        return True
    
    def rotate_cw(self, val):
        self.facing -= radians(val)
        return True
    
    def rotate_ccw(self, val):
        self.facing -= radians(val)
        return True
    
    def get_frame(self):
        return np.zeros((100, 100, 3), dtype=np.uint8)
    
    def get_state(self):
        return self.location
