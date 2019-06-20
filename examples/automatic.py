from fanshim import FanShim
import psutil
import argparse
import time


def update_led(state):
    if state:
        fanshim.set_light(0, 255, 0)
    else:
        fanshim.set_light(255, 0, 0)


def get_cpu_temp():
    return psutil.sensors_temperatures()['cpu-thermal'][0].current


def set_fan(status):
    global enabled
    changed = False
    if status != enabled:
        changed = True
        update_led(status)
        fanshim.set_fan(status)
    enabled = status
    return changed


def set_automatic(status):
    global armed, last_change
    armed = status
    last_change = 0


parser = argparse.ArgumentParser()
parser.add_argument('--threshold', type=float, default=37.0, help='Temperature threshold in degrees C to enable fan')
parser.add_argument('--hysteresis', type=float, default=2.0, help='Distance from threshold before fan is disabled')

args = parser.parse_args()

fanshim = FanShim()
fanshim.set_hold_time(1.0)
fanshim.set_fan(False)
armed = True
enabled = False
last_change = 0

t = get_cpu_temp()
if t >= args.threshold:
    last_change = get_cpu_temp()
    set_fan(True)


@fanshim.on_release()
def release_handler(was_held):
    global armed
    if was_held:
        set_automatic(not armed)
    elif not armed:
        set_fan(not enabled)


@fanshim.on_hold()
def held_handler():
    for _ in range(3):
        fanshim.set_light(0, 0, 255)
        time.sleep(0.04)
        fanshim.set_light(0, 0, 0)
        time.sleep(0.04)
        update_led(enabled)


try:
    update_led(fanshim.get_fan())
    while True:
        t = get_cpu_temp()
        print("Current: {:05.02f} Target: {:05.02f} Automatic: {} On: {}".format(t, args.threshold, armed, enabled))
        if abs(last_change - t) > args.hysteresis and armed:
            if set_fan(t >= args.threshold):
                last_change = t
        time.sleep(1.0)
except KeyboardInterrupt:
    pass
