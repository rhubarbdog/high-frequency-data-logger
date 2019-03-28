<h1>Logging Data at high frequencies</h1>
</br>
This requires 2 pyboards one measuring the data and transmitting it to a
second. The second pyboard writes the data to SD card. I have tried using a
Raspberry Pi to record the data but could not acheive the high baudrate
required to save time in the measure and transmit cycle.
</br>
</br>
One pyboard requires files <code>data_logger.py</code> and <code>
log_Tx.py</code>, the other <code>data_logger.py</code> and <code>log_Rx.py
</code>.  The pyboards communicate using UART so require the Tx terminal of
the "log_Tx" pyboard (pin Y1) to be connected to the Rx terminal of the
"log_Rx" pyboard (pin Y2). They also need to share a ground connection, if
they don't share a power source you need to connect GND on one pyboard to GND
on the other.
</br>
</br>
Using 1 pyboard v1.1 and 1 sensor I have acheived data rates of 5.6kHz passing
data from one uart to another. But am yet to get any where near that using 2
pyboards. The best acheivable is 1.2KHz with 1 sensor.
</br>
</br>
Program <code>log_Rx.py</code> starts by calling the <code>.begin()</code>
method. This method loops, press USR switch to terminate. You must call the
<code>.end(wait = 0)</code> method, it writes the remaining buffers to file and
closes it. It's best to set a wait time of a couple of seconds just to allow
all data transfers to have completed.
</br>
</br>
Press and release the USR switch to start the tranmitter <code>log_Tx.py
</code>. The transmitter calls the <code>.begin()</code> method and returns.
Keep it running with a loop controlled by pressing the USR switch to
terminate. The <code>.end()</code> method is optional it stops the tranmitter
and restores garbage collection.
</br>
</br>
Start the logger <code>log_Rx.py</code> before <code>log_Tx.py</code> it won't
record anything until the transmitter sends it. How ever if you allow <code>
log_Tx.py</code> to start first results will be missed and in the worst case
the data will be corrupt.
</br>
</br>
The transmitter <code>.logger_Tx()</code> has a <code>.timed()</code> method.
It's use is to determine the period in micro seconds of the  <code>
.transmit()</code> method. Using a REPL prompt or the <code>pyboard.py</code>
command initiate you logger with a guessed frequency. eg <code>log =
data_logger.logger_Tx(1, ('X1', 'X2', 'X3'), 12, 400)</code> sets up a
transmitter on UART 1 with 3 ADC pins using timer 12 at 400Hz. Make multiple
calls to <code>log.timed()</code> to determine the usual period and outlier
period. The fisrt call takes upto 25 micro seconds longer, this time isn't
repeated in the data set and can be ignored.
</br>
The reciever <code>.logger_Rx()</code> is used as follows <code>log =
data_logger.logger_Rx(6, 3, pyb.Switch(), '/sd/data.bin', pyb.LED(4))</code>.
The log object uses uart 6 and has 3 sensors. It is terminated  by pressing
the USR switch. <code>pyb.Switch()</code> could be a <code>pyb.Pin('X1',
pyb.Pin.IN, pyb.Pin.PULL_DOWN)</code> set the pin to high to terminate or the
software switch object below. The <code>log</code> object writes data to file
<code>/sd/data/bin</code>. LED 4 (blue) will be switched on whilst data is
being written to disk.
</br>
</br>
The class <code>.SoftSwitch()</code> is a software switch which has a <code>
.press()</code> method it is intended for this to be called from any
callback. Like <code>pyb.Switch()</code> it has a <code>.value()</code>
method like pressing the USR switch calling the <code>.press()<code> method
causes the <code>.value()</code> method return <code>True</code>.
</br>
</br>
To check the validity of the data set there is a python3 command <code>
anzbin.py</code>. It has 2 keyword parameters --sensors (the number of
sensors) and --freq (the sampling rate). Usage <code>python3 anzbin.py <i>
data-file.bin</i></code>