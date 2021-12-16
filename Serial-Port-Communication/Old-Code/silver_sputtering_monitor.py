#!/usr/bin/env python
# coding: utf-8
# author: Siwei Chen <siwei.chen.hts@gmail.com>

import datetime
import struct
import time

import serial

LOG_FILE = 'logs/log_{}.csv'.format(datetime.datetime.now().date().isoformat())

sp_pr = serial.Serial()
sp_pr.port = "com5"
sp_pr.baudrate = 19200
sp_pr.bytesize = 8
sp_pr.parity = serial.PARITY_NONE
sp_pr.stopbits = serial.STOPBITS_ONE
sp_pr.timeout = 1.0

sp_ps = serial.Serial()
sp_ps.port = "com2"
sp_ps.baudrate = 38400
sp_ps.bytesize = 8
sp_ps.parity = serial.PARITY_NONE
sp_ps.stopbits = serial.STOPBITS_ONE
sp_ps.timeout = 0.2


def start_pr():
    sp_pr.open()
    sp_pr.write(b"@253DLC!START;FF")
    sp_pr.close()


def stop_pr():
    sp_pr.open()
    sp_pr.write(b"@253DLC!STOP;FF")
    sp_pr.close()


def read_pr():
    sp_pr.open()
    buffer = ""
    while True:
        sp_pr.readall()
        sp_pr.write(b"@253DL?;FF")
        buffer = sp_pr.read(49)[2:].decode()
        if len(buffer) == 49-2:
            break
    sp_pr.close()
    try:
        return float(buffer.split(";")[2][:-2])
    except:
        return float(buffer.split(";")[2][:-2].split()[0])


def read_ps(u=780, i=1180, p=800):
    tosend = (
        [23, 255 - 23, 255, 255, 0, 0, 0x60, 0x40]
        + list(struct.pack("f", u))
        + list(struct.pack("f", i))
        + list(struct.pack("f", p))
        + [1]
    )
    s = sum(tosend[2:])
    tosend.append(s // 256)
    tosend.append(s % 256)
    #     for i in tosend:
    #         print(f'{i:x}')
    sp_ps.open()
    buffer = []
    while True:
        sp_ps.readall()
        sp_ps.write(tosend)
        buffer = sp_ps.read(39)
        if sum(buffer[2:-2]) == buffer[-2] * 256 + buffer[-1]:
            break
    sp_ps.close()
    rtn = (
        struct.unpack("f", bytes(buffer[10:14]))[0],
        struct.unpack("f", bytes(buffer[14:18]))[0],
        struct.unpack("f", bytes(buffer[18:22]))[0],
        buffer[25] * 256 + buffer[26],
        buffer[27] * 256 + buffer[28],
        buffer[29] * 256 + buffer[30],
    )
    return rtn


def main():

    try:
        start_pr()
        title = "date,time,pressure(mBar),Uact(V),Iact(mA),Pact(W),Im,UxI,dU\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(title)
        while True:
            pr = read_pr()
            Uact, Iact, Pact, Im, UxI, dU = read_ps()
            tn = datetime.datetime.now().isoformat(sep=",", timespec="seconds")
            s = f"{tn},{pr:0.2e},{int(Uact)},{int(Iact)},{int(Pact)},{Im},{UxI},{dU}"
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"{s}\n")
            for i, j in zip(
                [
                    "Date",
                    "Time",
                    "Pressure (mBar)",
                    "Voltage (V)",
                    "Current (mA)",
                    "Power(W)",
                    "Arc Count (I)",
                    "Arc Count (P)",
                    "Arc Count (dU)",
                ],
                [
                    tn.split(",")[0],
                    tn.split(",")[1],
                    f"{pr:0.2e}",
                    f"{Uact:0.0f}",
                    f"{Iact:0.0f}",
                    f"{Pact:0.0f}",
                    f"{Im}",
                    f"{UxI}",
                    f"{dU}",
                ],
            ):
                print(f"\33[92m{i:<16}\33[91m{j:<8}")
            print("\33[10A")
            # time.sleep(1)
    except Exception as e:
        print('\n\n\n\n\n\n\n\n\n')
        print(e)
    finally:
        if sp_pr.is_open:
            sp_pr.close()
        if sp_ps.is_open:
            sp_ps.close()
        stop_pr()
        
if __name__ == "__main__":
    main()
