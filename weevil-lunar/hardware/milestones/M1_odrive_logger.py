#!/usr/bin/env python3
"""
M1_odrive_logger.py

Safe, minimal ODrive S1 logging script for torque-first bringup.
Logs position, velocity, torque, current, temps at ~20 Hz.

Run in parallel with manual odrivetool commands or bringup guide.

Usage:
    python M1_odrive_logger.py [optional_log_prefix]

Ctrl+C to stop and save.
"""

import odrive
import time
import csv
from datetime import datetime
import argparse
import signal

# Configurable constants (tune as needed)
SAMPLE_RATE_HZ = 20.0  # 50 ms interval
LOG_FIELDS = [
    "timestamp_ms",
    "mode",
    "command_value",
    "measured_position_deg",
    "measured_velocity_deg_s",
    "measured_torque_Nm",
    "command_current_A",
    "measured_current_A",
    "motor_temp_C",
    "controller_temp_C",
    "notes",
]

# Global stop flag
running = True


def signal_handler(sig, frame):
    global running
    print(" Caught Ctrl+C — stopping logger and saving...")
    running = False


signal.signal(signal.SIGINT, signal_handler)


def main():
    parser = argparse.ArgumentParser(description="ODrive M1 bringup logger")
    parser.add_argument("prefix", nargs="?", default="m1_log", help="Log file prefix")
    args = parser.parse_args()

    # Connect to ODrive
    print("Searching for ODrive...")
    odrv = odrive.find_any()
    if not odrv:
        print("Error: No ODrive found. Check USB connection.")
        return

    axis = odrv.axis0
    print(f"Connected to ODrive (serial: {odrv.serial_number})")

    # Open CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{args.prefix}_{timestamp}.csv"

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(LOG_FIELDS)

        print(f"Logging started → {filename}")
        print("Press Ctrl+C to stop")

        start_time = time.time()

        while running:
            t_ms = int((time.time() - start_time) * 1000)

            # Safe read (skip if faulted)
            try:
                pos_deg = axis.encoder.pos_estimate * 360.0  # counts → degrees
                vel_deg_s = axis.encoder.vel_estimate * 360.0 / 60.0  # rpm → deg/s
                torque_nm = axis.motor.torque_estimate
                cmd_current = axis.controller.input_current
                meas_current = axis.motor.current_control.Iq_measured
                motor_temp = axis.motor.temperature
                ctrl_temp = odrv.controller_temp if hasattr(odrv, "controller_temp") else float("nan")
                mode = "torque"  # update manually if switching modes
                cmd_value = axis.controller.input_torque
                notes = ""  # manual annotation if needed
            except Exception as e:
                print(f"Read error: {e}")
                pos_deg = vel_deg_s = torque_nm = cmd_current = meas_current = motor_temp = ctrl_temp = float("nan")
                mode = cmd_value = notes = "ERROR"

            row = [
                t_ms,
                mode,
                cmd_value,
                pos_deg,
                vel_deg_s,
                torque_nm,
                cmd_current,
                meas_current,
                motor_temp,
                ctrl_temp,
                notes,
            ]
            writer.writerow(row)
            f.flush()
            time.sleep(1.0 / SAMPLE_RATE_HZ)

    print(f"Logging stopped. Saved: {filename}")


if __name__ == "__main__":
    main()
