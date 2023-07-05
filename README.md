### Megatec Platinen Test

## Installation
```
git clone https://github.com/AndreasScharf/megatec-platinen-test.git test
pip3 install -r requirements.txt

mkdir /home/pi/TestLogs

```

## Autostart

```
mkdir /home/pi/.config/autostart/

cd /home/pi/.config/autostart/

echo '[Desktop Entry]
Name=PlatinenTest
Type=Application
Comment=Megatec Platinen Test
Exec=/usr/bin/python3 /home/pi/test/index.py' > /home/pi/.config/autostart/test.desktop

chmod +x /home/pi/.config/autostart/test.desktop
```
# Details 
die Anleitung habe ich von hier
https://medium.com/@arslion/starting-python-gui-program-on-raspberry-pi-startup-56fb4e451cc1


## Konfiguration
Grundfos Sensor Seriennummer für Serielle Kommunikation
```
GFS_SERIAL_NUMBER = '99455960-01-228-00498'
```

## Ausführen ohne Autostart
```
python3 index.py
```

## Senden in eueren Netzwerkordner
In der index.py Zeile 606 kann der Sigi gerne einen kleinen Block für eure Netzwerkablage machen
Oder Ihr gebt mir die nötigen Infos und ich mache es euch rein

