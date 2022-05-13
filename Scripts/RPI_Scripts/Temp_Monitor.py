from os import popen
from psutil import virtual_memory, cpu_percent
from time import sleep
from datetime import datetime as dt


def GetStats():
    try:
        return f'{measure_temp()}{measure_ram_percent()}{measure_cpu()}'.replace("temp=", "")
    except Exception as e:
        return ""


def measure_temp():
    try:
        temp = popen("vcgencmd measure_temp").readline()
        temp.replace("'C", ' °C')
        return f"current CPU temp: {temp}"
    except Exception as e:
        return ""


def get_ram_percent():
    return virtual_memory().percent


def measure_ram_percent():
    return f"RAM in use: {get_ram_percent()}%\n"


def get_cpu_percent():
    return cpu_percent()


def measure_cpu():
    return f"CPU load:{get_cpu_percent()}%"


def GetDateTime():
    return dt.now()


def GetDateTimeStringify(format="%H:%M:%S %p"):
    return GetDateTime().strftime(format)


if __name__ == '__main__':
    i = 1
    highest_ram = get_ram_percent()

    while True:
        current_ram = get_ram_percent()
        if current_ram > highest_ram:
            highest_ram = current_ram

        print(
            f'----------\nIteration {i}:\ntime: {GetDateTimeStringify()}\n{GetStats()}\nHighest ram: {highest_ram}%')

        i += 1
        sleep(1)
