#!/usr/bin/python
import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk

from app_components import navigator 
from functools import partial

import math


from datetime import datetime

import sys

GFS_SERIAL_NUMBER = '99455960-01-228-00498'
PATH_TO_DOCS = '/home/pi/TestLogs'

hw = sys.argv[1] if len(sys.argv) >= 2 else 'pi'
path = './' if len(sys.argv) >= 2 and sys.argv[1] == 'win' else '/home/pi/Documents/test'

if not hw == 'win':
    
    from python_anopi import AnoPi
    import board
    from gpio_expander import expander
    from DAC_MCP4726 import DAC
    from grundfossensor import grundfossensor as gfs

    from mobil_com import mobilcom



def main():
    window = tk.Tk()
    window.title("Megatec Test")
    window.geometry("800x400")
    window.attributes("-fullscreen", True)

    window_panel = tk.Frame(window, height=400, width=800)
    window_panel.pack(fill=tk.X, expand=False)
    
    def quit():
        window.destroy()
    # Create a window and pass it to the Application object
    App(window_panel, "Megatec Test", quit)

class Log():
    def __init__(self, window):
        self.serialnr = tk.StringVar(window)
        
        self.i2cAdressen = tk.StringVar(window)
        self.i2c = []
        
        self.digtal_inputs = ['def'] * 8
    
        self.digtal_outputs = ""

        self.analog_inputs = ""
        self.analog_output_current = ""
        self.analog_output_voltage = ""

        self.gfs_lane1 = "GFS Sensor Linie 1 Init: Failed"
        self.gfs_lane2 = "GFS Sensor Linie 1 Init: Failed"

        self.simnr = "0"
        
    def print(self):
        i2c_txt = ''
        for e in self.i2c:
            i2c_txt = i2c_txt + '{}: {}\n'.format(hex(e[0]), e[1]) 
        
        di_txt = ''
        for i in range(len(self.digtal_inputs)):
            e = self.digtal_inputs[i]
            di_txt = di_txt + 'DI{}: {}\n'.format(i, e)
        
        now = datetime.now()  # current date and time
        date = now.strftime('%Y-%m-%d %H:%M:%S')
            
        return """
### Hardware Test Platine {serialnr} ###
Test am {date}

### I2C Adressen ###
{i2c}

### Digital Inputs ###
{di}

### Digital Outputs ###
{do}

### Analog Inputs ###
{ai}

### Analog Output Current ###
{aoc}
### Analog Output Voltage ###
{aov}

### GFS Lane 1 ###
{gfs0}
### GFS Lane 2 ###
{gfs1}

### SIM Karten Nummer ###
{sim} 


""".format(
                serialnr=self.serialnr.get(),
                i2c=i2c_txt, 
                di=di_txt, 
                do=self.digtal_outputs,
                ai=self.analog_inputs,
                
                aoc = self.analog_output_current,
                aov=self.analog_output_voltage,
                
                gfs0=self.gfs_lane1,
                gfs1=self.gfs_lane2,

                sim=self.simnr,
            date=date
                )
        

# Code to add widgets will go here...
class App:
    def __init__(self, window, title, quit):
        self.window = window
        self.looper = None
        
        self.quit = quit
        self.page_index = 0
        
        self.log = Log(window)
        self.navigator = navigator(self.window)
        
        self.navigator.back = None
        self.navigator.next = None

        self.body = tk.Frame(master=self.window, height=200, width=300)
        self.body.pack()
        
        self.printBtn = tk.Button(master=self.window, text="Print", command=self.log.print)
        self.printBtn.pack()

        self.loadGreeting()
        self.window.mainloop()

    
    def clearFrame(self, frame):
        if self.looper:
            frame.after_cancel(self.looper)
        
        # destroy all widgets from frame
        for widget in frame.winfo_children():
            widget.destroy()
        
    def loadGreeting(self):
        self.clearFrame(self.body)
        self.navigator.setTitle("Willkommen :)")

        
        greeting = tk.Label(master=self.body, text="Hallo Wilkommen zur Platinen Test\n Seriennummer bitte eingeben")
        greeting.pack()
        
        
        product_nr = tk.Entry(master=self.body, textvariable=self.log.serialnr)
        product_nr.pack()
        
        img = Image.open(path + '/assets/frapp_logo_mit_schrift.png')
        img = img.resize((100, 75))
        self.frapplogo_pic = ImageTk.PhotoImage(img, master=self.window)
        frapplogo = tk.Label(
            self.body, image=self.frapplogo_pic, height=75, width=100)
        frapplogo.pack()
        
        def next():
            if not self.log.serialnr.get() == '':
                self.loadI2CAdresses()
        
        self.navigator.back = None
        self.navigator.next = next

    def loadI2CAdresses(self):
        self.clearFrame(self.body)

        self.navigator.setTitle("I2C Adressen")

       
        
        neededI2CAdresses = [0x20, 0x21, 0x46, 0x47, 0x48, 0x49, 0x4a, 0x4b, 0x63]
        
        i2cLabels = []
        
        for i2c in neededI2CAdresses:
            label = tk.Label(master=self.body, fg='black', font=("Arial", 16), text="{}".format(hex(i2c)))
            label.pack()
            i2cLabels.append(label)
            
            self.log.i2c.append([i2c, 'def'])
        
        i2c = 0
        if not hw == 'win':
            i2c = board.I2C()
           
        def readI2CAdresses(i):
            try:
                while not i2c.try_lock():
                   pass
                if not hw == 'win':

                    list_i2c = i2c.scan()
                    
                    if i < len(neededI2CAdresses):
                        if neededI2CAdresses[i] in list_i2c:
                            i2cLabels[i].configure(fg='green')
                            self.log.i2c[i][1] = 'ok'
                        i = i + 1

            finally:  # unlock the i2c bus when ctrl-c'ing out of the loop
                if not hw == 'win':
                    
                    i2c.unlock()
        
            
            self.looper = self.body.after(200, lambda : readI2CAdresses(i))

        readI2CAdresses(0)
            
        self.navigator.back = self.loadGreeting
        self.navigator.next = self.loadDigitalInputs
        
    def loadDigitalInputs(self):
        self.clearFrame(self.body)
        self.navigator.setTitle("Digitale Eingänge")
     
        
        info = tk.Label(
            master=self.body, text="Brücke alle Digitalen Eingänge auf 24V")
        info.pack(pady=5)
        
        digital_inputs = []
        
        for i in range(8):
            label = tk.Label(master=self.body, fg='black', font=( "Arial", 16), text="DI {}".format(i))
            label.pack()
            
            digital_inputs.append(label)
            
        io_expander = 0
        if not hw == 'win':
            io_expander = expander(0x20)
        
        def readDigitalInputs():
            print('read digital inputs')
            
            if not hw == 'win':
                read_byte = io_expander.read()
                for i in range(8):
                    di = digital_inputs[i]
                    if (read_byte & (0x1 << i)) and 1:
                        di.configure(fg='green')
                        
                        self.log.analog_inputs[i] = 'ok'
                        
          
            self.looper = self.body.after(1000, readDigitalInputs)
            
        readDigitalInputs()
        
        self.navigator.back = self.loadI2CAdresses
        self.navigator.next = self.loadDigitalOutputs
        
    def loadDigitalOutputs(self):
        self.clearFrame(self.body)
        self.navigator.setTitle("Digitale Ausgänge")
       
        info = tk.Label(
            master=self.body, text="Schalte alle Digitalen Ausgänge \n mit weiter bestätigen das alle Relais geschalten baben")
        info.pack()
        
        io_expander = 0
        if not hw == 'win':
            io_expander = expander(0x20)
        def toogleOutput(e):
            
            # toggle color of the output button
            if digital_outputs[e].cget('bg') == 'grey':
                digital_outputs[e].configure(bg='green')
            else:
                digital_outputs[e].configure(bg='grey')
                
            # build write word of green btn labels
            if not hw == 'win':

                word = 0
                for i in range(8):
                    word = word | (digital_outputs[i].cget('bg') == 'green' and True) << i
                print(word)
                io_expander.write_port_A(word)
            
        digital_outputs = []
        
        # wrapper for digital out COM 0-3 
        left_frame = tk.Frame(master=self.body)
        left_frame.pack(side='left')
        for i in range(4):
            btn = tk.Button(master=left_frame, fg='black', bg='grey', font=(
                "Arial", 16), text="DO {}".format(i), command=partial(toogleOutput, i))
            btn.index = i
            btn.pack()

            digital_outputs.append(btn)
            

        # wrapper for digital out COM 4-7
        right_frame = tk.Frame(master=self.body)
        right_frame.pack(side='right')
        for i in range(4, 8):
            btn = tk.Button(master=right_frame, fg='black', bg='grey', font=(
                "Arial", 16), text="DO {}".format(i),  command=partial(toogleOutput, i))
            btn.pack()
            btn.index = i


            digital_outputs.append(btn)
  
        def next():
            now = datetime.now()  # current date and time

            self.log.digtal_outputs = 'Digitale Outputs haben alle geschalten \nBestätigt um {}'.format(
                now.strftime('%Y-%m-%d %H:%M:%S'))
            self.loadAnalogInputs()
        
        self.navigator.back = self.loadDigitalInputs
        self.navigator.next = next
        
    def loadAnalogInputs(self):
        
        
        self.clearFrame(self.body)
        self.navigator.setTitle("Analoge Eingänge")
        
        ais = []
        if not hw == 'win':
            a = AnoPi(adresses=[0x46, 0x48, 0x47, 0x4B, 0x49, 0x4A])
        
        for i in range(6):
            l = Label(master=self.body, text="AI {}: \t{:.2f}V \t{:.2f}mA".format(
                i, 0.0, 0.0), font=("Arial", 16))


            l.pack()
            ais.append(l)
            
        def readDigitalInputs():
            print('read analog inputs')
            
            for i in range(6):
                (v, mA) = (0, 4)
                if not hw == 'win':
                    (v, e) = a.ai_V(i)
                    (mA, e) = a.ai_mA(i)

                ais[i].configure(text="AI {}: \t{:.2f}V \t{:.2f}mA".format(i, v, mA))
                        
          
            self.looper = self.body.after(1000, readDigitalInputs)
            
        readDigitalInputs()
        
        def next():
            now = datetime.now()  # current date and time

            self.log.analog_inputs = 'Alle Analogen Eingänge sind funktionsfähig \nBestätigt um {}'.format(
                now.strftime('%Y-%m-%d %H:%M:%S'))
            self.loadAnalogOutputsCurrent()
            
        self.navigator.back = self.loadDigitalOutputs
        self.navigator.next = next
        
    def loadAnalogOutputsCurrent(self):
        self.clearFrame(self.body)
        self.navigator.setTitle("Analog Ausgang Strom")

        info = tk.Label(
            master=self.body, text="Messe 16.80mA auf zwischen Iout(X10.3) und GND(X10.4) Klemme \nmit weiter Messung bestätigen")
        info.pack(pady=5)
        
        
        if not hw == 'win':
            io_expander_dac = expander(0x21, 0x00)
            io_expander_dac.write_port_A(0x80)  # 4-20mA output
            
            dac = DAC()
            dac.write(80) #make 80 percent on the current output
        
        def next():
            now = datetime.now()  # current date and time

            self.log.analog_output_current = 'Am Analogen Stromausgang wurden 16.8mA gemessen\nBestätigt um {}'.format(
                now.strftime('%Y-%m-%d %H:%M:%S'))
            self.loadAnalogOutputsVoltage()

        self.navigator.back = self.loadAnalogInputs
        self.navigator.next = next
        
    def loadAnalogOutputsVoltage(self):
        self.clearFrame(self.body)
        self.navigator.setTitle("Analog Ausgang Spannung")

        info = tk.Label(
            master=self.body, text="Messe 8.00V auf zwischen Vout(X10.2) und GND(X10.4) Klemme \nmit weiter Messung bestätigen")
        info.pack(pady=5)


        if not hw == 'win':
            io_expander_dac = expander(0x21, 0x00)
            io_expander_dac.write_port_A(0x80)  # 0-10V output
            
            dac = DAC()
            dac.write(80) #make 80 percent on the current output
            
        def next():
            now = datetime.now()  # current date and time

            self.log.analog_output_voltage = 'Am Analogen Voltausgang wurden 8.00V gemessen\nBestätigt um {}'.format(
                now.strftime('%Y-%m-%d %H:%M:%S'))
            self.loadGFSLane1()

        self.navigator.back = self.loadAnalogInputs
        self.navigator.next = next

    def loadGFSLane1(self):
        self.clearFrame(self.body)
        self.navigator.setTitle("Grundfos Sensor Lane 1")

        self.gfs_pressure = float('NaN')
        self.gfs_tempertatur = float('NaN')

        info_wrapper = tk.Frame(master=self.body)
        info_wrapper.pack(fill=tk.X)
        
        info_wrapper_horizontal = tk.Frame(master=info_wrapper)
        info_wrapper_horizontal.pack(side=tk.LEFT)
        
        info = tk.Label(
            master=info_wrapper_horizontal, text="Sobald der Sensor an X9.0-3 angeklemmt \nist \"Lesen\" Drücken")
        info.pack(pady=5, side=tk.LEFT)
        
        img = Image.open(path + '/assets/gfs_lane1.png')
        img = img.resize((200, 130))
        self.info_pic_image = ImageTk.PhotoImage(img, master=info_wrapper)
        info_pic = tk.Label(
            info_wrapper, image=self.info_pic_image, height=130, width=200)
        info_pic.pack(side=tk.LEFT)
        
      
        
        readBtn = tk.Button(
            master=self.body, text="Lesen", bg='lightblue', font=("Arial", 16), command=lambda: self.initGFS(0)
        )
        readBtn.pack(pady=5, side=tk.LEFT)
        
        gfs_status = tk.Label(
            master=self.body, text="Grundfos Sensor Status".format(), font=("Arial", 16))
        gfs_status.pack(pady=5)
        
        gfs_status_temp = tk.Label(
            master=self.body, text="T: {:.2f}°C".format(0), font=("Arial", 16))
        gfs_status_temp.pack(pady=5)
        
        gfs_status_pressure = tk.Label(
            master=self.body, text="P: {:.2f}bar".format(0), font=("Arial", 16))
        gfs_status_pressure.pack(pady=5)
        
        def setGFSStatus():
           
            gfs_status_temp.configure(text="T: {:.2f}°C".format(
                self.gfs_tempertatur), fg='green' if not math.isnan(self.gfs_tempertatur) else 'black')
            gfs_status_pressure.configure(text="P: {:.2f}bar".format(
                self.gfs_pressure), fg='green' if not math.isnan(self.gfs_pressure) else 'black')

            self.looper = self.body.after(1000, setGFSStatus)


        setGFSStatus()

      
        self.navigator.back = self.loadAnalogOutputsVoltage
        self.navigator.next = self.loadGFSLane2
       
    def loadGFSLane2(self):
        self.clearFrame(self.body)
        self.navigator.setTitle("Grundfos Sensor Lane 2")

        self.gfs_pressure = float('NaN')
        self.gfs_tempertatur = float('NaN')

        info_wrapper = tk.Frame(master=self.body)
        info_wrapper.pack(fill=tk.X)

        info_wrapper_horizontal = tk.Frame(master=info_wrapper)
        info_wrapper_horizontal.pack(side=tk.LEFT)

        info = tk.Label(
            master=info_wrapper_horizontal, text="Sobald der Sensor an X9.4-7 angeklemmt \nist \"Lesen\" Drücken")
        info.pack(pady=5, side=tk.LEFT)

        img = Image.open(path + '/assets/gfs_lane2.png')
        img = img.resize((200, 130))
        self.info_pic_image = ImageTk.PhotoImage(img, master=info_wrapper)
        info_pic = tk.Label(
            info_wrapper, image=self.info_pic_image, height=130, width=200)
        info_pic.pack(side=tk.LEFT)
        
        
        readBtn = tk.Button(
            master=self.body, text="Lesen", bg='lightblue', font=("Arial", 16), command=lambda: self.initGFS(1)
        )
        readBtn.pack(pady=5, side=tk.LEFT)

        gfs_status = tk.Label(
            master=self.body, text="Grundfos Sensor Status".format(), font=("Arial", 16))
        gfs_status.pack(pady=5)

        gfs_status_temp = tk.Label(
            master=self.body, text="T: {:.2f}°C".format(0), font=("Arial", 16))
        gfs_status_temp.pack(pady=5)

        gfs_status_pressure = tk.Label(
            master=self.body, text="P: {:.2f}bar".format(0), font=("Arial", 16))
        gfs_status_pressure.pack(pady=5)

        def setGFSStatus():

            gfs_status_temp.configure(text="T: {:.2f}°C".format(
                self.gfs_tempertatur), fg='green' if not math.isnan(self.gfs_tempertatur) else 'black')
            gfs_status_pressure.configure(text="P: {:.2f}bar".format(
                self.gfs_pressure), fg='green' if not math.isnan(self.gfs_pressure) else 'black')

            self.looper = self.body.after(1000, setGFSStatus)

        setGFSStatus()

      
        self.navigator.back = self.loadGFSLane1
        self.navigator.next = self.loadMobilSim
       
    def initGFS(self, lane):
        if not hw == 'win':
            sn = GFS_SERIAL_NUMBER
            s = gfs(lane, sn, 0x01, 'MFS')
            
            self.gfs_pressure = s.get_pressure()
            self.gfs_tempertatur = s.get_temperatur()
            
            if (not s.error) and not lane:
                self.log.gfs_lane1 = """GFS Sensor Linie 1 Init: Success \nPressure: {}bar \nTemperatur: {}°C""".format(self.gfs_pressure, self.gfs_tempertatur) 
            elif (not s.error) and lane:
                self.log.gfs_lane2 = """GFS Sensor Linie 2 Init: Success \nPressure: {}bar \nTemperatur: {}°C""".format(
                    self.gfs_pressure, self.gfs_tempertatur)
                
        pass

    def loadMobilSim(self):
        self.clearFrame(self.body)
        self.navigator.setTitle("Mobil SIM")
        
        info = tk.Label(
            master=self.body, text="SIM Karte eingelegen")
        info.pack(pady=5)
        
        sim_nr = tk.Label(master=self.body, text='SIM: {}'.format(self.log.simnr), font=("Arial", 16))
        sim_nr.pack()
        
        if not hw == 'win':
            mc = mobilcom()
        
        def setSimStatus():

            if not hw == 'win':
                self.log.simnr = mc.getSimNr()
                if not self.log.simnr == '0':
                    sim_nr.configure(text='SIM: {}'.format(self.log.simnr), fg='green')
            self.looper = self.body.after(1000, setSimStatus)

        setSimStatus()
        
        self.navigator.back = self.loadGFSLane2
        self.navigator.next = self.loadLog
        
        
    def loadLog(self):
        self.clearFrame(self.body)
        self.navigator.setTitle("Test Abgeschlossen")
        
        info = tk.Label(
            master=self.body, text="Netzwerkstecker (RJ45) eingesteckt? \nBericht senden?")
        info.pack(pady=5)


        def sendLog():
            info.configure(
                text='Netzwerkstecker (RJ45) eingesteckt? \nBericht senden...')
            
            txt = self.log.print()
            
            f = open('{}/{}.txt'.format(PATH_TO_DOCS, self.log.serialnr.get()), 'w')
            f.write(txt)
            f.close()
            # hier kann sigi seinen code für sftp dateisystem/email o.ae. einfügen?
            
            
            
        
        sendBtn = tk.Button(
            master=self.body, text="Senden", bg='lightblue', font=("Arial", 16), command=sendLog
        )
        sendBtn.pack(pady=5)
        
        self.navigator.back = self.loadMobilSim
        self.navigator.next = self.quit
        
if __name__ == "__main__":
    main()