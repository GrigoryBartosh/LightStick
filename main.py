from __future__ import division
import time
from os import listdir
import re
from PIL import Image
from neopixel import *

FILE_CONFIG = "config.txt"
FOLDER_IMGS = "photo/"

LED_COUNT   = 143
LED_PIN     = 18
LED_FREQ_HZ = 800000
LED_DMA     = 10
LED_INVERT  = False
LED_CHANNEL = 0

PREFIX = "                   "
COMMANDS = [PREFIX + "ls .................. list of images",
            PREFIX + "ld IMG_NAME ......... load image",
            PREFIX + "p AFTER(OPT)......... play image",
            PREFIX + "st RED GREAN BLUE ... set color for all strip",
            PREFIX + "br BRIGHTNESS ....... set brightness of the strip",
            PREFIX + "dr DIRECTION ........ set the direction of reading the image",
            PREFIX + "or .................. change orientation",
            PREFIX + "dl MILLISECONDS...... delay",
            PREFIX + "off ................. turn off the strip",
            PREFIX + "e ................... exit"]

def read_config():
    brightness, direction, orientation, delay = 0, "", "", 0

    with open(FILE_CONFIG, 'r') as file:
        lines = file.read().splitlines()
        brightness = int(lines[0])
        direction = lines[1]
        orientation = lines[2]

    return brightness, direction, orientation, delay

def write_config(brightness=None, direction=None, orientation=None, delay=None):
    src_brightness, src_direction, src_orientation, src_delay = read_config()

    if brightness == None:
        brightness = src_brightness
    if direction == None:
        direction = src_direction
    if orientation == None:
        orientation = src_orientation
    if delay == None:
        delay = src_delay

    with open(FILE_CONFIG, 'w') as file:
        file.write(str(brightness) + "\n")
        file.write(direction + "\n")
        file.write(orientation + "\n")
        file.write(str(delay) + "\n")

def strip_init(brightness):
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, brightness, LED_CHANNEL)
    strip.begin()
    return strip

def make_color(r, g, b):
    return Color(g, r, b)

def strip_set(arr):
    for i in xrange(strip.numPixels()):
        strip.setPixelColor(i, arr[i])
    strip.show()

def strip_turn_off():
    strip_set([0 for x in xrange(LED_COUNT)])

def change_lines_orientation(lines):
    new_lines = []
    for line in lines:
        new_lines.append(line[::-1])

    return new_lines

def get_img_file_name(img_name):
    exp1 = "^" + img_name + "\..*$"
    exp2 = "^" + img_name + "$"

    lst = listdir(FOLDER_IMGS)

    try:
        num = int(img_name) - 1
        if num < 0 or len(lst) <= num:
            raise
        return FOLDER_IMGS + lst[num]
    except ValueError as e:
        for file_name in lst:
            if re.match(exp1, file_name) != None or re.match(exp2, file_name) != None:
                return FOLDER_IMGS + file_name

        raise

def load_img(img_name, direction, orientation):
    img_file_name = get_img_file_name(img_name)

    img = Image.open(img_file_name)

    if direction == "^" or direction == "v":
        img = img.rotate(270, expand=1)

    w, h = img.size
    w = w * LED_COUNT // h
    h = LED_COUNT
    im_small = img.resize((w, h))
    im_small_rgb = im_small.convert('RGB')

    lines = []
    for x in xrange(w):
        line = []
        for y in xrange(h):
            r, g, b = im_small_rgb.getpixel((x, y))
            line.append(make_color(r, g, b))

        lines.append(line)

    if direction == "v" or direction == "<":
        lines = lines[::-1]

    if orientation == "d":
        lines = change_lines_orientation(lines)

    return lines

def play(lines, delay):
    n = len(lines)
    for line in lines:
        strip_set(line)
        time.sleep(delay / 1000.0)

    strip_turn_off()

if __name__ == '__main__':
    brightness, direction, orientation, delay = read_config()
    strip = strip_init(brightness)
    img_lines = []

    while True:
        params_itr = iter(raw_input("Enter the command: ").split(" "))
        command = next(params_itr)

        if command == "ls":
            lst = listdir(FOLDER_IMGS)
            num = 0
            for file_name in lst:
                num += 1
                print PREFIX + str(num) + ". " + file_name

        elif command == "ld":
            try:
                img_name = next(params_itr)
            except:
                print PREFIX + "Enter the name of the image or its number in the list"
                continue

            try:
                img_lines = load_img(img_name, direction, orientation)
                print PREFIX + "Image '" + img_name + "' uploaded"
            except:
                print PREFIX + "Image '" + img_name + "' was not found"

        elif command == "p":
            after_time = 0
            try:
                after_time = int(next(params_itr))
            except:
                pass

            if len(img_lines) == 0:
                print PREFIX + "Image not uploaded"
            else:
                time.sleep(after_time)
                play(img_lines, delay)
                print PREFIX + "Playback complete"

        elif command == "st":
            try:
                r = min(max(0, int(next(params_itr))), 255)
                g = min(max(0, int(next(params_itr))), 255)
                b = min(max(0, int(next(params_itr))), 255)
            except:
                print PREFIX + "Enter three colors"
                continue

            strip_set([make_color(r, g, b) for x in xrange(LED_COUNT)])
            print PREFIX + "Color was set"

        elif command == "br":
            try:
                brightness = min(max(0, int(next(params_itr))), 255)
            except:
                print PREFIX + "Enter the brightness value"
                continue

            strip = strip_init(brightness)
            write_config(brightness=brightness)
            print PREFIX + "Brightness was changed to: " + str(brightness)

        elif command == "dr":
            new_direction = ""
            try:
                new_direction = next(params_itr)
            except:
                print PREFIX + "Enter the brightness value"
                continue

            if new_direction not in ["<", "v", ">", "^"]:
                print PREFIX + "Unacceptable direction"
                continue

            if direction == new_direction:
                print PREFIX + "direction already has a value: " + direction
            else:
                img_lines = []
                direction = new_direction
                write_config(direction=direction)
                print PREFIX + "Direction was changed to: " + direction
                print PREFIX + "Now you must reload the image"

        elif command == "or":
            img_lines = change_lines_orientation(img_lines)
            orientation = "d" if orientation == "u" else "u"
            write_config(orientation=orientation)
            print PREFIX + "Orientation was changed to: " + orientation

        elif command == "dl":
            try:
                delay = max(0, int(next(params_itr)))
            except:
                print PREFIX + "Enter the brightness value"
                continue

            write_config(delay=delay)
            print PREFIX + "Delay was changed to: " + str(delay)

        elif command == "off":
            strip_turn_off()
            print PREFIX + "The strip was turned off"

        elif command == "h":
            for c in COMMANDS:
                print c

        elif command == "e":
            strip_turn_off()
            print PREFIX + "Goodbye!"
            break

        else:
            print PREFIX + "Unknown command"

        print ""