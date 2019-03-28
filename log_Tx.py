import pyb
import data_logger

log = data_logger.logger_Tx(6 ,('X1',), 12, 2600)
switch = pyb.Switch()
yellow = pyb.LED(3)

def main():
    # press and release USR switch
    while not switch.value():
        pass
    pyb.delay(50)
    while switch.value():
        pass


    log.begin()
    yellow.on()
    while not switch.value():
        pyb.delay(1000)
    log.end()
    yellow.off()

if __name__ == '__main__':
    main()
