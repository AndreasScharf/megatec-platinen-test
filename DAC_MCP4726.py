from smbus2 import SMBus
from gpio_expander import expander
import time

class DAC(object):

    def __init__(self):
        self.DAC_bus = SMBus(1)  # 1 steht für das I2C Interface 
        time.sleep(1) #kurz warten um 121 IO Error zu verhindern (!)
        self.address = 0x63 #Adresse bei dieser Gehäuseform
        self.config_byte = 0x78 #Aktiviert beim Schreiben Vref (wichtig!)
        self.full_range = 4095 #12-Bit DAC
        print("Setup of DAC done.")

    def write(self, percent_value):

        print(percent_value)
        percent_value = percent_value/100        
        X_out = int(round(self.full_range*percent_value)) #X steht für Volt (V) oder Ampere (I)
        data1 = (X_out >> 4)
        data2 = (X_out & 15) << 4
        data = [data1, data2] #Beispiel Wert: [0xFF, 0xF0]

        """
        OSError: [Errno 121] Remote I/O Error ist am Anfang ab uns zu aufgetreten.
        Aber nur beim DAC. Ca. alle 20 - 30 Schreibzyklen.
        
        """
        try:     
            self.DAC_bus.write_i2c_block_data(self.address, self.config_byte, data)
        except OSError as e:
            print("Fehler DAC", e)
            self.once_only=0
            pass

"""
#Nur zum einzeln Testen
#init des Expanders vorm DAC
#ao_expander = expander(0x21)
#ao_expander.write_port_A(0x80)

analog_converter = DAC()
while(1):
    for i in range(0, 110, 10):
        analog_converter.write(i)
        time.sleep(2)
        print(i)
        #x = ao_expander.read()
        #print("Port B:" + hex(x))
        """


