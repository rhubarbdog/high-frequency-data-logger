#!/usr/bin/python3

import struct
import argparse

command = argparse.ArgumentParser(description='data logger analysis')
command.add_argument('file', help='the binary file to examine')
command.add_argument('-s', '--sensors', default=1, type=int,\
                     help='the number of sensors sampled')
command.add_argument('-f' ,'--freq', default=1200, type=int,\
                     help='the sampling frequency')

args = command.parse_args()

input_ = args.file
sensor_pins = args.sensors
freq  = args.freq
FORMAT  = '=ii' + ('i' * sensor_pins) + 'i'

period = 1000000 // freq
slew = 0
fine = 0
count = 0
begin = 0
minimum = 0
maximum = 0
sigma = 0
with open(input_, 'rb') as inp:
    buffer_ = bytearray(inp.read(struct.calcsize(FORMAT)))
    numbers = struct.unpack(FORMAT, buffer_)
    count += 1
    if numbers[0] != count:
        print("Missing or corrupt packet id", numbers[0], "!=", count)
    begin = numbers[1]
    minimum = numbers[2]
    maximum = numbers[2]
    sigma += numbers[2]

    if numbers[-1] < 0:
        print('bad crc',count)
        
    while True:
        try:
            buffer_ = bytearray(inp.read(struct.calcsize(FORMAT)))
            numbers = struct.unpack(FORMAT, buffer_)
        except:
            break
        count += 1
        if numbers[0] != count:
            print("Missing or corrupt packet id", numbers[0], "!=", count)
            break

        if numbers[-1] < 0:
            print('bad crc',count)
            break
        
        break_twice = False
        for n in range(2, len(numbers) - 1):
            if numbers[n] > 4095 or numbers[n] < 0:
                print("Corrupt sensor (%d) data :" % (n - 1), numbers[n])
                break_twice = True
                break

        if break_twice:
            break
        minimum = min(numbers[2], minimum)
        maximum = max(numbers[2], maximum)
        sigma += numbers[2]

        if (numbers[1] > 0 and begin < 0):
            diff = abs(numbers[1]) + abs(begin)
        elif (numbers[1] < 0 and begin > 0):
            diff = (2**29 - abs(numbers[1])) + (2**29 - abs(begin))
        else:
            diff = numbers[1] - begin

        if diff > period + 2  or diff < period - 2:
            fine += 1
            
        if abs(period - diff) > period / 33.3:
            print('Period slew @', count, numbers[1], begin, diff)
            slew += 1
        
        begin = numbers[1]
        
print('count', count)
print('fine', fine - slew)
print('slew' , slew)
print('min', minimum)
print('max', maximum)
print('mean', sigma/count)
