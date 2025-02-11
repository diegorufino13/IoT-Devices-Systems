import time
import json
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO

# Set up GPIO pins for pump control
pump_pin = 21
GPIO.setmode(GPIO.BCM)
GPIO.setup(pump_pin, GPIO.OUT)

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)
# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)
# Create single-ended input on channel 0
chan = AnalogIn(ads, ADS.P0)

# Calibration function
def calibrate_sensor():
    max_val = None
    min_val = None

    baseline_check = input("Is Capacitive Sensor Dry? (enter 'y' to proceed): ")
    if baseline_check == 'y':
        max_val = chan.value
        print("------{:>5}\t{:>5}".format("raw", "v"))
        for _ in range(10):
            if chan.value > max_val:
                max_val = chan.value
            print("CHAN 0: "+"{:>5}\t{:>5.3f}".format(chan.value, chan.voltage))
            time.sleep(0.5)

    print('\n')

    water_check = input("Is Capacitive Sensor in Water? (enter 'y' to proceed): ")
    if water_check == 'y':
        min_val = chan.value
        print("------{:>5}\t{:>5}".format("raw", "v"))
        for _ in range(10):
            if chan.value < min_val:
                min_val = chan.value
            print("CHAN 0: "+"{:>5}\t{:>5.3f}".format(chan.value, chan.voltage))
            time.sleep(0.5)

    config_data = {
        "full_saturation": min_val,
        "zero_saturation": max_val
    }

    with open('cap_config.json', 'w') as outfile:
        json.dump(config_data, outfile)
    print('\n')
    print(config_data)

# Translation function
def percent_translation(raw_val):
    with open("cap_config.json") as json_data_file:
        config_data = json.load(json_data_file)
    per_val = abs((raw_val - config_data["zero_saturation"]) / (config_data["full_saturation"] - config_data["zero_saturation"])) * 100
    return round(per_val, 3)

# Main function
def main():
    try:
        calibrate_sensor()  # Calibrate the sensor

        print("----------  {:>5}\t{:>5}".format("Saturation", "Voltage\n"))
        while True:
            sensor_percent = percent_translation(chan.value)
            print("SOIL SENSOR: " + "{:>5}%\t{:>5.3f}".format(sensor_percent, chan.voltage))

            if sensor_percent < 30:
                GPIO.output(pump_pin, GPIO.HIGH)  # Turn on pump
                print("Pump activated!")
            else:
                GPIO.output(pump_pin, GPIO.LOW)  # Turn off pump

            time.sleep(1)

    except KeyboardInterrupt:
        print('Exiting script')
    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    main()