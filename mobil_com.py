import serial
import time
import RPi.GPIO as GPIO
import socket
import usb.core




interrupted = False
def current_milli_time(): return int(round(time.time() * 1000))


#GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# turn on mobil
#GPIO.setmode(GPIO.BOARD) is allready in BCM
GPIO.setmode(GPIO.BCM)
MOBIL_PWR_PIN = 26
GPIO.setup(MOBIL_PWR_PIN, GPIO.OUT)
serialCom = 0

class mobilcom:
    def __init__(self):
        self.usbcoms = ['/dev/ttyUSB2', '/dev/ttyUSB4']
        self.usbcomerror = 0
        self.connectSerialCom(0)
        pass
    
    def getSimNr(self):
        (anwser, e) = self.sendMessage("AT+ICCID")
        txt = anwser.split('ICCID:')
        print(txt)
        nr = (txt[1].split('\r\n\r') if len(txt) > 1 else ['0'])[0]
        print(nr)
        return nr

    
    def telitModuleActived(self):
        dev = usb.core.find(find_all=1)
        for cfg in dev:
            if cfg.idVendor == 0x1bc7 and (cfg.idProduct & 0x1200) == 0x1200:
                print('Mobil Module Attached')
                return True

        return False


    def connectSerialCom(self, i):
        com_index = 0
        com_open_success = False
        while not com_open_success:
            try:
                print('Try open COM on', self.usbcoms[com_index])
                self.serialCom = serial.Serial(
                    port=self.usbcoms[com_index],
                    baudrate=115200,
                    timeout=None)
                com_open_success = True
            except Exception as e:
                print(e)
                com_index += 1
                if com_index > len(self.usbcoms):
                    com_index = 0
                    time.sleep(60)


    
    def restartTelitModule(self):
        print('restart module by hard reset')
        GPIO.output(MOBIL_PWR_PIN, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(MOBIL_PWR_PIN, GPIO.LOW)
        print('restarted')
        while not self.telitModuleActived():
            time.sleep(1)
        print('wait for serial com')
        time.sleep(1)
        self.connectSerialCom(1)

    def sendMessage(self, m):

        m = m + '\r'
        writesuccessful = False
        while not writesuccessful:
            try:
                self.serialCom.reset_input_buffer()
                self.serialCom.write(m.encode())
                writesuccessful = True
                self.usbcomerror = 0
            except KeyboardInterrupt:
                print('KeyboardInterrupt exception is caught')
                return ''
            except Exception as e:
                print('write unsuccessful', e)
                self.usbcomerror = self.usbcomerror + 1
                if self.usbcomerror > 10:
                    self.usbcomerror = 0
                    self.restartTelitModule()
                elif self.usbcomerror > 5:
                    # connect no next larger
                    global currentSerialCom
                    currentSerialCom = int(
                        not currentSerialCom)  # toogle serial com
                    self.connectSerialCom(currentSerialCom)

                time.sleep(1)

        time.sleep(0.51)
        wd_for_timeout = current_milli_time()
        response = ''
        while 1:
            biw = self.serialCom.inWaiting()
            if biw:
                response += self.serialCom.read(biw).decode('utf-8')

                if '\r' in response:
                    return (response, None)

            if current_milli_time() - wd_for_timeout > 30 * 1000:
                print('Timeout', m)
                return (None, 'Timeout')
'''

if __name__ == "__main__":
    mc = mobilcom()
    print(mc.getSimNr())
'''       
