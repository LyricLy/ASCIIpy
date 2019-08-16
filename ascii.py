#!/usr/bin/env python3

import argparse
import subprocess
import string
import math

from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont


DEFAULT_CHARS = string.ascii_letters + string.digits + string.punctuation + " "
DEFAULT_FONT = "Consolas"


def get_font(font_name):
    filename = subprocess.check_output(["fc-match", font_name]).decode().split(":")[0]
    if filename == "arial.ttf" and font_name.lower() not in ("arial", "sans-serif"):
        print("WARNING: Font name may be misspelled.")
    return ImageFont.truetype(filename, 12)

def make_mapping(charset, font, invert):
    float_mapping = {}
    for char in charset:
        x, y = font.getsize(char)
        if y > 11:
            continue
        im = Image.new("L", (x, y), color=255 if invert else 0)
        draw = ImageDraw.Draw(im)
        draw.text((0, 0), char, font=font, fill=0 if invert else 255)
        avg = math.sqrt(sum(x ** 2 for x in im.getdata()) / (x * y))
        float_mapping[avg] = char
    mn, mx = min(float_mapping), max(float_mapping)
    mapping = []
    for n in range(256):
        total = min(float_mapping.items(), key=lambda x: abs(n / 255 - (x[0] - mn) / (mx - mn)))
        mapping.append(((total[0] - mn) / (mx - mn), total[1]))
    return mapping, (x, y)

def convert(im, mapping, ratio, dither):
    width, height = im.size
    text = []
    c = 0
    offsets = defaultdict(int)
    for i, px in enumerate(im.convert(mode="L").getdata()):
        if i % width == 0:
            text.append([])
        c += ratio
        chars, c = divmod(c, 1)
        if dither:
            new_px = px + offsets[i]
            value, char = mapping[min(max(int(new_px), 0), 255)]
            error = new_px - value * 255
            if i+1 % width != 0:
                offsets[i+1] += error * (7 / 16)
                offsets[i+width+1] += error * (1 / 16)
            if i % width != 0:
                offsets[i+width-1] += error * (3 / 16)
            offsets[i+width] += error * (5 / 16)
        else:
            char = mapping[px][1]
        text[-1].extend([char] * int(chars))
    return "\n".join("".join(l) for l in text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert an image or sequence of images to text.")
    parser.add_argument("input_file", help="Image to convert to ASCII.")
    parser.add_argument("output_file", help="File to save the result to.")
    parser.add_argument("-i", "--invert", action="store_true", help="Target black on white instead of white on black.")
    parser.add_argument("-f", "--font", default=DEFAULT_FONT, help="The font to target. Defaults to Consolas.")
    parser.add_argument("-s", "--spacing", default=0, type=int, help="The line spacing, in pixels, to target. Defaults to 0.")
    parser.add_argument("-c", "--charset", default=DEFAULT_CHARS, help="The set of valid characters to use. Defaults to printable ASCII.")
    parser.add_argument("-r", "--resize", nargs=2, type=int, default=None, help="The resolution to resize the image to. Defaults to no resizing.")
    parser.add_argument("-t", "--text", action="store_true", help="Output a text file.")
    parser.add_argument("-nd", "--no-dither", action="store_true", help="Don't apply dithering to the output.")
    args = parser.parse_args()
    
    print("Generating mapping...")
    font = get_font(args.font)
    mapping, (fx, fy) = make_mapping(args.charset, font, args.invert)

    print("Performing conversion...")
    im = Image.open(args.input_file)
    if args.resize:
        im = im.resize(args.resize)
    text = convert(im, mapping, (fy + args.spacing) / fx, not args.no_dither)

    if args.text:
        with open(args.output_file, "w") as f:
            f.write(text)
    else:
        print("Converting to image...")
        size = ImageDraw.Draw(Image.new("1", (0, 0))).multiline_textsize(text, font=font, spacing=args.spacing)
        im = Image.new("L", size, color=255 if args.invert else 0)
        draw = ImageDraw.Draw(im)
        draw.multiline_text((0, 0), text, font=font, fill=0 if args.invert else 255, spacing=args.spacing)
        im.save(args.output_file)
