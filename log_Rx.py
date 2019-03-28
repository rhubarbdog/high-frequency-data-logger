import pyb
import data_logger

kill_switch = data_logger.SoftSwitch()

pyb.Switch().callback(lambda:kill_switch.press())

log = data_logger.logger_Rx(6, 1, kill_switch, '/sd/data-set.bin', \
                            pyb.LED(4))
def main():

    pyb.LED(3).on()
    log.begin()
    log.end(5000)
    pyb.LED(3).off()

if __name__ == '__main__':
    main()
