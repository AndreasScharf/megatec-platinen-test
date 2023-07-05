import os
import serial
import time

class grundfossensor(object):
    """docstring for grundfossensor."""

    def __init__(self, serial, barcode, sensor_id, type, my_os='L'):
        self.ports = []
        self.use_port = ''
        self.my_os = my_os
        if my_os == 'L':
          """
          for item in os.listdir("/dev/"):
             if 'USB' in item :
                 self.ports.append('/dev/' + item)
          """
          self.ports = ['/dev/ttyS0', '/dev/ttyAMA1']
          self.ports = [self.ports[serial]]
          print('build up')
        elif my_os == 'W':
          self.ports = ['COM3']

        self.ser = serial
        self.barcode = barcode
        self.sensor_id = sensor_id
        self.type = type
        self.error = True

        self.fullscale_tempratur = 0
        self.fullscale_pressure = 0
        self.fullscale_flow = 0

        self.pressure_list = []

        self.init(barcode, sensor_id)
        print('init done')
        

    def init(self, barcode, sensor_id):
        self.try_again = False
        self.ser = None
        if not self.use_port == '':
            self.ports = {self.use_port}
        
        for port in self.ports:
          try:
            self.ser = serial.Serial(
                port=port,
                baudrate = 9600,
                timeout=None)
          except Exception as e:
            os.system('tput reset > {}'.format(port))
            
          code = []
          temp_code = ''
          for c in barcode:
            if c == '-':
                continue
            elif temp_code == '':
                temp_code = c
            else:
                temp_code = temp_code + c
                code.append(int(temp_code, 16))
                temp_code = ''


          self.message = [ 0x72, 0x10 , 0xEE, 0x01, 0x09 ]#warum nicht 0x02
          for c in code:
            self.message.append(c)

          self.message.append(self.sensor_id)
          self.message.append(self.checksum(self.message))
          #try:
          self.print_message(self.message)
          self.ser.write(bytearray(self.message))
          anwser = self.listen()
          print('anwser', anwser)
          # Check Sensor Barcode
          
          sensor_barcode_correct = False
          if str(anwser[5:-2]) == str(code):
            sensor_barcode_correct = True
          else:
            print('Wrong Barcode')
          
          
          if (anwser == 'Error' or anwser == 'Timeout') and sensor_barcode_correct:
            continue
          else:
            
            self.error = False
            print('port', port, barcode, anwser)
            self.use_port = port
            break
          
        if self.error:
          print('init problem with: {}, {}'.format(barcode, self.ports))

        self.try_again = True

    def change_baudrate(self, baudrate):
      b_id = [1200, 4800, 9600, 19200, 56000 if not self.type == 'MFS' else 57600, 11520]    
      b_index = b_id.index(baudrate)
      
      self.message = [0x72, 0x06, self.sensor_id, 0x01, 0x00, b_index]
      self.message.append(self.checksum(self.message))
      
      self.ser.write(self.message)
      anwser = self.listen()
      self.ser.setBaudrate(baudrate)
      return
    
    def ieee_bin_to_float(self, zahl):
      v = zahl >> 31
      exp = (zahl & 0x7F800000) >> 23
      man = (zahl & 0x007FFFFF)

      e = float(exp) - float(2 ** (8 - 1) - 1)
      m = 1 + float(man) / float(2 ** 23)

      return (-1) ** v * m * 2 ** e
    def checksum(self, bytes_to_send):
      sum = 0
      for b in bytes_to_send:
        sum = sum + b

      while sum >= 0x100:
        sum = sum - 0x100
      return sum
    def calculate(self, fullscale, value):
        if fullscale == 'Error':
          return 'Error'
        try:
          if value > 0x8000 :
            x = float( float(value) - 2 ** 16)  / (2 ** 14) * fullscale
            return x
          elif value < 0x8000 :
            x = float( value ) / (2 ** 14) * fullscale
            return x
          else:
            return 'Error'
        except:
          print(fullscale, value)
          return 'Error'
    def build_anwser(self, timeout):
      STX = bytes([0x72])[0]
      anwser = bytearray()
      anwser_length = 0
      length_index = 1
      #states
      wait_for_STX, wait_for_length, building_anwser = True, False, False

      while 1:
          bytes_in_Waiting = self.ser.inWaiting()
          if bytes_in_Waiting > 0:
            data = self.ser.read(size=bytes_in_Waiting)
            #print(data)
            
            if wait_for_STX and STX in data:
              wait_for_STX, wait_for_length = False, True
              stx_index = data.index(STX)
              length_index = 1
              data = data[stx_index: len(data)]
            if wait_for_length:
              if len(data) > length_index:
                anwser_length = data[length_index]
                wait_for_length, building_anwser = False, True
              else:
                length_index = 0
                continue  # length is in next round
            if building_anwser and anwser_length > 0:
              if anwser_length > len(data):
                a = data[0: len(data)]
                anwser.extend(a)
                anwser_length = anwser_length - len(data)
              else:
                anwser.extend(data[0: anwser_length])
                anwser_length = 0
            if building_anwser and anwser_length <= 0 and len(anwser):
              return anwser, None
          elif timeout < time.time():
            return None, 'Timeout'
    
    def listen(self):
      MAX_TIMEOUT = 5
      ERROR_TRYS = 5
      
      start_reading = time.time()
      valid_anwser = False
      time.sleep(0.5)#give sensor time to process message
      failed_anwsers = 0
      while 1:
        anwser, err = self.build_anwser(start_reading + MAX_TIMEOUT)
        if not err:
          #self.print_message(anwser)
          sended_checksum = anwser.pop()
          if self.checksum(anwser) == sended_checksum:
            anwser.append(sended_checksum)
            return anwser
          else:
            err = 'Message Wrong'
        if err:
          self.ser.flush()
          self.ser.write(self.message)
          print('send again', err)
          failed_anwsers += 1
          time.sleep(0.5)
          if failed_anwsers > MAX_TIMEOUT:
            return 'Error'
    
    def listen1(self):
        timeouts = 100  # Error modus
        isHeader = False
        buffer = []
        trys = 0
        while 1:
            trys = trys + 1
            bytes_in_Waiting = self.ser.inWaiting()
            if bytes_in_Waiting > 0:
                if not isHeader:
                    buffer = []

                data = self.ser.read(size=bytes_in_Waiting)
                for c in data:
                   if isinstance(c, int):
                       buffer.append(c)
                   else:
                       buffer.append(ord(c))

                if isHeader and not data[0] == 0x72:
                   if not buffer[-1] == self.checksum(buffer[:-1]):
                       self.ser.write(self.message)
                       return self.listen()

                   trys = 0
                   return buffer
                else:
                  isHeader = buffer[0] == 0x72
            

    def request_fullscale(self, data_id):
        self.message = [ 0x72, 0x06, self.sensor_id, 0x02, data_id ]
        self.message.append(self.checksum(self.message))
        try:
          self.ser.write(self.message)
        except:
          self.error = True
          return 'Error' 
        data = self.listen()
        try:
          x = (data[-2] << 24) + (data[-3] << 16) + (data[-4] << 8) + data[-5]
          return self.ieee_bin_to_float(x)
        except Exception as e :
          print(e)
    def get_temperatur(self):
      if self.error :
        self.init(self.barcode, self.sensor_id)
        if self.error: # ist nach initiasierung immer noch error hat init nicbt geklappt
            return 'Error'

      if self.fullscale_tempratur == 0 or not self.fullscale_tempratur:
        self.fullscale_tempratur = self.request_fullscale(0x03)

      self.message = [0x72, 0x07, self.sensor_id, 0x00, 0x04, 0x00]
      self.message.append(self.checksum(self.message))

      
      try:
        self.ser.write(self.message)
      except:
        self.error = True
        return 'Error'

      data = self.listen()
      
      if data == 'Timeout':
          self.error = True
          return 'Error'

      value = (data[-3] << 8) + data[-2]

      return self.calculate(self.fullscale_tempratur, value)
    def get_pressure(self):
      if self.type == 'VFS': #VFS kann keinen Druck
        return 'Error'

      if self.error :
        self.init(self.barcode, self.sensor_id)
        if self.error: # ist nach initiasierung immer noch error hat init nicbt geklappt
            return 'Error'

      if self.fullscale_pressure == 0 or not self.fullscale_pressure:
        self.fullscale_pressure = self.request_fullscale(0x04)

      self.message = [0x72, 0x07, self.sensor_id, 0x00, 0x01, 0x00]
      self.message.append(self.checksum(self.message))

      try:
        self.ser.write(self.message)
      except:
        self.error = True
        return 'Error'
      data = self.listen()

      if data == 'Timeout':
         self.error = True
         return 'Error'

      value = (data[-3] << 8) + data[-2]

      return self.calculate(self.fullscale_pressure, value)
    def get_flow(self):
        if self.type == 'RPS': #VFS kann keinen Druck
            return 'Error'

        if self.error :
            self.init(self.barcode, self.sensor_id)
            if self.error: # ist nach initiasierung immer noch error hat init nicbt geklappt
                return 'Error'

        if self.fullscale_flow == 0:
            self.fullscale_flow = self.request_fullscale(0x08)

        self.message = [0x72, 0x07, self.sensor_id, 0x00, 0x10, 0x00]
        self.message.append(self.checksum(self.message))

        try:
          self.ser.write(self.message)
        except:
          self.error = True
          return 'Error'

        data = self.listen()

        if data == 'Timeout':
          self.error = True
          return 'Error'

        value = (data[-3] << 8) + data[-2]

        return self.calculate(self.fullscale_flow, value)


    def print_message(self, message):
      print(  '[{}]'.format(', '.join(' 0x{:02x}'.format(x) for x in message)))
    

class sensor(object):
    def __init__(self, serialnr, sensor_id, sensor_status):
        self.serialnr = serialnr
        self.sensor_id = sensor_id
        self.sensor_status = sensor_status
        self.instance = 0
        
        self.init()

    def init(self):
        self.sensor_status.set(0)

        sn = self.serialnr.getString()
        if not sn == '0':
            self.instance = grundfossensor(None, sn, self.sensor_id, 'MFS')
            if self.instance.error:
              self.sensor_status.set(2)
            else:
              self.sensor_status.set(1)

        else:
            self.sensor_status.set(0)
            
    def update(self):
      if ((not self.instance) or not self.instance.barcode == self.serialnr.getString()) and not self.serialnr.getString() == '0':
        self.init()

      
