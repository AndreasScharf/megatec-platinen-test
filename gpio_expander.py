"""
Benutze Bibliothek: pip install smbus2
Dokumentation:  https://smbus2.readthedocs.io/en/latest/
                https://pypi.org/project/smbus2/

"""


from smbus2 import SMBus
import time
import RPi.GPIO as GPIO


class expander(object):
    # Adresse 0x20 = Digital In & OUT; Adresse = 0x21 = GFS & Analog Out
    def __init__(self, adress, interrupt_byte=0x00):

        self.bus = SMBus(1)  # 1 steht für das I2C Interface 
        time.sleep(1) #kurz warten um 121 IO Error zu verhindern (!)

        self.DEVICE = adress  # Device Adresse (A0-A2)
        self.interrupt_byte = interrupt_byte
        self.interrupt_fired = False       

        # Register Adressen des Expanders, immer PORTA und B im Wechsel
        # Direction Register Eingang/Ausgang
        self.IODIRA = 0x00  
        self.IODIRB = 0x01  
        # Interrrupts werden mit dem Register aktiviert (Interrupt on change Register)
        self.GPINTENRA = 0x04
        self.GPINTENRB = 0x05
        # Gegen welchen Wert soll interrupt veglichen werden (Default compare Register)
        self.DEFVALA = 0x06
        self.DEFVALB = 0x07
        # Daten müssen auf 1 sein um mit DEFVAL verglichen zu werden
        self.INTCONA = 0x08  
        self.INTCONB = 0x09
        # Konfiguarations Register, siehe Docu
        self.IOCONA = 0x0A  
        self.IOCONB = 0x0B
        # Speichert den Pegelelvel der Pins bei Interrupt (read only)
        self.INTCAPA = 0x10
        self.INTCAPB = 0x11
        # Auslesen IMMER über GPIO Register (Eingabe)
        self.GPIOA = 0x12  
        self.GPIOB = 0x13
        # Schreiben IMMER über OLAT Register (Ausgabe)
        self.OLATA = 0x14  
        self.OLATB = 0x15

        """        
        DEFVAL-Register mit Änderung von 1 --> 0 muss noch getestet werden. (Interrupt)
        """

        if self.DEVICE == 0x20:  # Konfiguration für DI und DO
            # Port A komplett als Ausgang (0x00)
            self.bus.write_byte_data(self.DEVICE, self.IODIRA, 0x00)
            # Port B komplett als Eingang (0xFF)
            self.bus.write_byte_data(self.DEVICE, self.IODIRB, 0xFF)  
            #Welche Pin(s) von Port A als Interrupt fungieren wird mit self.interrupt_byte festgeleget
            self.bus.write_byte_data(self.DEVICE, self.GPINTENRA, self.interrupt_byte)
            # Testprogramm: 0x00 (Interrupt löst bei Änderung von 0 --> 1 aus)
            # Für Trägerplatine: self.interrupt_byte (Interrupt löst bei Änderung von 1 --> 0 aus)
            self.bus.write_byte_data(self.DEVICE, self.DEFVALA, self.interrupt_byte)
            # Vergleich mit DEFVAL 
            self.bus.write_byte_data(self.DEVICE, self.INTCONA, self.interrupt_byte)
            # IOCON = 0x42, falls Interrupt ansonsten 0x00 (!) siehe Docu
            self.bus.write_byte_data(self.DEVICE, self.IOCONA, 0x42) 
            self.bus.write_byte_data(self.DEVICE, self.IOCONB, 0x00)  
            # Zunächst alle Ausgangs-Pins auf 0
            self.bus.write_byte_data(self.DEVICE, self.OLATB, 0x00)
            # Zur Sicherheit, auslesen, falls interrupt aufgetreten und
            # er vorm beenden des Programms nicht zurückgesetzt werden konnte
            self.bus.read_byte_data(self.DEVICE, self.GPIOA)

            """GPIOs des RP festlegen für Interrupt"""
            # not needed in test for test use BCM
            # self.interrupt_pin = 29  # ACHTUNG: Bei Trägerplatine ist es Pin 29 (GPIO 5)
            # GPIO.setmode(GPIO.BOARD)  # Zählweise nach Pins nicht nach GPIOs  
            self.interrupt_pin = 5  # ACHTUNG: Bei Trägerplatine ist es Pin 29 (GPIO 5)

            GPIO.setup(self.interrupt_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Pin 29/GPIO 5 als Eingang festlegen            

            print("Setup of DI_DO_Expander done.")



        if self.DEVICE == 0x21: #Konfiguration für GFS und Analog Out (AO)
            self.bus.write_byte_data(self.DEVICE, self.IODIRA, 0x00) #Port A komplett als Ausgang
            self.bus.write_byte_data(self.DEVICE, self.IODIRB, 0x7F) #Port B Pin 7 als Ausgang, rest Eingang
            self.bus.write_byte_data(self.DEVICE, self.GPINTENRA, 0x00) #Zur Sicherheit auf 0 setzen
            self.bus.write_byte_data(self.DEVICE, self.DEFVALA, 0x00) #Zur Sicherheit auf 0 setzen
            self.bus.write_byte_data(self.DEVICE, self.INTCONA, 0x00) #Zur Sicherheit auf 0 setzen
            self.bus.write_byte_data(self.DEVICE, self.IOCONA, 0x00) #Siehe Docs
            self.bus.write_byte_data(self.DEVICE, self.IOCONB, 0x00) #siehe Docs

            """
            Konfiguration des GFS und AO Expanders:
            - Für Grundfusssensor(port=OLATB) ist byte_value = 0x80 (Ein) oder 0x00 (Aus)
            - Konfiguration des AD5751 für 0 - 10V:
                - port = self.OLATA und byte_value = 0x86
            - Konfiguration des AD5751 für 4 - 20 mA:
                - port = self.OLATA und byte_value = 0x80
            
            Standardmäßig werden in der init der AD5751 (Verstärker + I/V Wandler) auf
            Spannungsausgang (V) gesetzt und die GFS Spannung aktiviert
            Dies kann später über write_port_A bzw. write_port_B geändert werden            
            """
            self.bus.write_byte_data(self.DEVICE, self.OLATA, 0x86)#AD5751
            self.bus.write_byte_data(self.DEVICE, self.OLATB, 0x80)#GFS

            print("Setup of AO_GFS_Expander done.")
            

        



    def setupInterrupt(self, interrupt_handler):
        def callback_int_on_pin(channel):
            v = self.bus.read_byte_data(self.DEVICE, self.GPIOA)
            # if abfrage auf null oder isnt callable
            self.interrupt_fired = True
            interrupt_handler(v)

        GPIO.add_event_detect(self.interrupt_pin, GPIO.FALLING,
                              callback=callback_int_on_pin, bouncetime=50)

    def read(self):
        if self.interrupt_fired:
            self.bus.read_byte_data(self.DEVICE, self.GPIOB)
            self.interrupt_fired = False

        byte_value = self.bus.read_byte_data(self.DEVICE, self.GPIOB)
        return byte_value

    def write_port_A(self, byte_value):

        self.bus.write_byte_data(self.DEVICE, self.OLATA, byte_value)


    def write_port_B(self, byte_value):

        self.bus.write_byte_data(self.DEVICE, self.OLATB, byte_value)



