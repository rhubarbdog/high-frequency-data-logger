import pyb
import time
import array
import ustruct
# These 2 are for performace and consistency. use of
# .enable_irq() and disable.irq() take longer but improve
# consistency
import gc
import machine

import micropython
micropython.alloc_emergency_exception_buf(200)

SHORT_CHAR = 'h'
HEADER_FORMAT = '<ii' + SHORT_CHAR
SIZE_OF_HEADER = ustruct.calcsize(HEADER_FORMAT)
SHORT_FORMAT = '<' + SHORT_CHAR
SIZE_OF_SHORT = ustruct.calcsize(SHORT_FORMAT)
SIZE_OF_INT = ustruct.calcsize('<i')
BUFFER_SIZE = const(1024)
BAUD = const(450000)
BITS = const(8)

class SoftSwitch():
    def __init__(self):
        self.release()

    def value(self):
        return self._value

    def press(self):
        self._value = True

    def release(self):
        self._value = False

class logger_Tx():
    def __init__(self, uart, sensor_pins, timer, freq):
        self.data_points = len(sensor_pins)
        self.buffer_ = bytearray(((self.data_points - 1) * SIZE_OF_SHORT)\
                                 + SIZE_OF_HEADER)
        
        self.timer = pyb.Timer(timer, freq = freq)

        self.sensors = []
        for sp in sensor_pins:
            self.sensors.append(pyb.ADC(sp))

        self.uart = pyb.UART(uart, BAUD, BITS, parity = None, stop =1,\
                             timeout = 0, flow = 0, timeout_char = 0)

    def begin(self):
        gc.disable()
        self.check = 0
        self.start = time.ticks_us()
        self.timer.counter(0)
        self.timer.callback(self.transmit)

    def end(self):
        self.timer.callback(None)
        gc.enable()

    def timed(self):
        gc.disable()
        self.check = 0
        self.start = time.ticks_us()
        self.transmit(None)
        end = time.ticks_us()
        gc.enable()

        return  time.ticks_diff(end, self.start)
    
    @micropython.native
    def transmit(self, timer):
        machine.disable_irq()
        
        self.check += 1
        ustruct.pack_into(HEADER_FORMAT, self.buffer_, 0, self.check,\
                         time.ticks_diff(time.ticks_us(), self.start),
                         self.sensors[0].read())

        index = SIZE_OF_HEADER

        for s in range(1, self.data_points):
            ustruct.pack_into(SHORT_FORMAT, self.buffer_, index,\
                              self.sensors[s].read())
            index += SIZE_OF_SHORT

        self.uart.write(self.buffer_)
        
        machine.enable_irq()

class logger_Rx():
    def __init__(self, uart, data_points, kill_switch, file_name,\
                 write_LED = None):
        self.uart = pyb.UART(uart, BAUD, BITS, parity = None, stop =1,\
                             timeout = 0, flow = 0, timeout_char = 0,\
                             read_buf_len = BUFFER_SIZE * SIZE_OF_INT * 4)
        self.data_points = data_points + 2
        self.format_ = HEADER_FORMAT
        if data_points > 1:
            self.format_ += (SHORT_CHAR * (data_points - 1))
        self.size_of_format = ustruct.calcsize(self.format_)
        self.file_ = open(file_name, 'wb')
        self.buffer_ = array.array('i', [0 for _ in range(BUFFER_SIZE)])
        self.index = 0 
        self.switch = kill_switch
        self.error = False
        self.LED = write_LED
        if not self.LED is None:
            self.LED.off()
            
        scalar = (16 * 1024) // self.size_of_format
        ring_buffer = bytearray(self.size_of_format * (scalar + 128))
        self.ring = memoryview(ring_buffer)
        self.ring_max = len(ring_buffer)
        self.put = 0
        self.get = 0
        self.looped = False

    @micropython.native
    def ring2array(self):
        numbers = ustruct.unpack(self.format_,\
                                 self.ring[self.get: self.get +\
                                           self.size_of_format])

        if self.index + self.data_points < BUFFER_SIZE:
            for n in numbers:
                self.buffer_[self.index] = n
                self.index += 1
        else:
            delta = BUFFER_SIZE - self.index
            for d in range(delta):
                self.buffer_[self.index] = numbers[d]
                self.index += 1

            if self.LED:
                self.LED.on()
            self.file_.write(self.buffer_)
            if self.LED:
                self.LED.off()
            self.index = 0
            for n in numbers[delta:]:
                self.buffer_[self.index] = n
                self.index += 1

        self.get += self.size_of_format
        if self.get >= self.ring_max:
            self.get = 0
            self.looped = False
        
    @micropython.native
    def begin(self):
        gc.enable()
        while not self.switch.value():
            amount = self.uart.any() 
            if amount > 0:
                getting = self.put + amount 
                if getting >= self.ring_max:
                    get_twice = True
                    getting = self.ring_max
                else:
                    get_twice = False

                self.uart.readinto(self.ring[self.put:getting])

                if get_twice:
                    self.looped = True
                    self.put = self.put + amount - self.ring_max
                    self.uart.readinto(self.ring[:self.put])
                else:
                    self.put = getting
                    
                if self.looped and self.put >= self.get:
                    self.error = True
                    self.file_.close()
                    return None

            while self.looped or self.get + self.size_of_format < self.put:
                self.ring2array()
    
    def end(self, wait_ms = 0):
        if self.error:
            return None
        
        if wait_ms > 0:
            time.sleep_ms(wait_ms)
            
        while self.looped or self.get + self.size_of_format < self.put:
            self.ring2array()
        
        amount = self.uart.any() 
        if amount > 0:
            getting = self.put + amount 
            if getting >= self.ring_max:
                get_twice = True
                getting = self.ring_max
            else:
                get_twice = False

            self.uart.readinto(self.ring[self.put:getting])

            if get_twice:
                self.looped = True
                self.put = self.put + amount - self.ring_max
                self.uart.readinto(self.ring[:self.put])
            else:
                self.put = getting

            if self.looped and self.put >= self.get:
                self.error = True
                self.file_.close()
                return None

        while self.looped or self.get + self.size_of_format < self.put:
            self.ring2array()

        if self.index > 0:
            self.file_.write(self.buffer_[:self.index])

        if self.put != self.get:
            self.error = True

        self.file_.close()
