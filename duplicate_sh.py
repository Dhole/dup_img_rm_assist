#!/usr/bin/env python3

import sys
import math
import subprocess
from tkinter import *
from PIL import Image, ImageTk, ImageFont, ImageDraw

filename = sys.argv[1]
# Global
script_filename = sys.argv[2]

print("""
Key bindings:
- left/right arrow: go to previos/next image
- [1-9]: select images to save
- enter: confirm numeric selection
- d: save only the first image
- s: save all images (don't delete any)
- w: write deletion script
""")

# Global
images_repeats = []

lines = []
with open(filename, 'r') as f:
    for line in f:
        if line == '\n':
            images_repeats.append(lines)
            lines = []
            continue
        lines.append(line[:-1])

# Global
images_save = [list(range(len(images_repeats[i]))) for i in range(len(images_repeats))]

# Write output script to keep saved images and delete the rest
def write_output(script_filename, images_repeats, images_save):
    with open(script_filename, 'w') as out_file:
        out_file.write('#!/bin/sh\n\n')

        for i in range(len(images_repeats)):
            out_file.write(f'# {images_save[i]}\n')
            for j in range(len(images_repeats[i])):
                line = f'rm \'{images_repeats[i][j]}\'\n'
                if j in images_save[i]:
                    out_file.write(f'# {line}')
                else:
                    out_file.write(f'{line}')
            out_file.write('\n')

class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.pack(fill=BOTH, expand=1)
        
        self.msg = '           Press any key           '
        self.label1 = Label(self, text=self.msg, width=len(self.msg), bg='yellow')
        self.label1.pack(side='bottom')
        self.msg_state = '           Press any key           '
        self.label2 = Label(self, text=self.msg_state, width=len(self.msg_state), bg='yellow')
        self.label2.pack(side='bottom')
        self.img_widgets = []

        self.nums = set()

        self.index = -1 

        self.master.bind('<Key>', self.key)

    # Store a selection of images for the current index
    def output(self, action):
        # global out_file
        global images_save
        global images_repeats
        
        image_repeats = images_repeats[self.index]
        save = []
        if action == 'd':
            save = [0]
        elif action == 's':
            save = list(range(len(image_repeats)))
        else:
            for i in action:
                save.append(i-1)

        images_save[self.index] = save

    # Render the images of the current index
    def render_image(self, image_repeats):
        global images_save
        for widget in self.img_widgets:
            widget.destroy()
        self.img_widgets = []

        font = ImageFont.truetype('DejaVuSansMono-Bold.ttf', size=18)
        font_small = ImageFont.truetype('DejaVuSansMono-Bold.ttf', size=14)

        (win_width, win_height) = (self.winfo_width(), self.winfo_height())
        max_height = win_height - 64

        cols = min(len(image_repeats), 5)
        rows = math.ceil(len(image_repeats) / cols)
        max_width = int(win_width / cols)
        max_height = max_height / rows

        x = 0
        y = 0
        for i in range(len(image_repeats)):
            img_filename = image_repeats[i]
            print(f'Showing {img_filename}')
            image = Image.open(img_filename).convert('RGBA')
            width = int(max_width)
            height = int(image.height * (width / image.width))
            if height > max_height:
                height = int(max_height)
                width = int(image.width * (height / image.height))
            image = image.resize((width, height))
            # txt = Image.new('RGBA', image.size, (255,255,255,0))
            d = ImageDraw.Draw(image)
            d.text((8, 8), f'{i+1}', font=font, fill=(255, 255, 255, 255), stroke_fill=(0, 0, 0, 255), stroke_width=2)
            d.text((8, height - 32), img_filename, font=font_small, fill=(255, 255, 255, 255), stroke_fill=(0, 0, 0, 255), stroke_width=2)
            # image = Image.alpha_composite(image, txt)
            render = ImageTk.PhotoImage(image)
            img = Label(self, image=render)
            self.img_widgets.append(img)
            img.image = render
            x = (i % cols) * max_width
            y = (i // cols) * max_height
            print(f'({i % cols}, {i // cols}) -> ({x}, {y})')
            img.place(x=x, y=y)
        print()
        self.msg_state = f'{self.index+1}/{len(images_repeats)} save: {[i + 1 for i in images_save[self.index]]} ({len(images_repeats[self.index])})'
        self.label2.config(text=self.msg_state)

    # Show next set of images (inc index)
    def show_next(self):
        global images_repeats

        if self.index == len(images_repeats) -1:
            return
        self.index += 1
        self.render_image(images_repeats[self.index])

    # Show previous set of images (dec index)
    def show_prev(self):
        global images_repeats

        if self.index == 0:
            return
        self.index -= 1
        self.render_image(images_repeats[self.index])

    # Handle key events
    def key(self, event):
        show_next = False
        if event.char == event.keysym:
            if event.char in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                num = int(event.char)
                if num not in self.nums:
                    self.nums.add(num)
                else:
                    self.nums.remove(num)
                self.msg = f'{self.nums}'
            elif event.char == 'd':
                self.msg = 'delete all but first'
                self.output('d')
                show_next = True
            elif event.char == 's':
                self.msg = 'skip delete'
                self.output('s')
                show_next = True
            elif event.char == 'c':
                self.msg = 'clear selection'
                self.nums = set()
            elif event.char == 'w':
                self.msg = 'output script written'
                global script_filename
                global images_repeats
                global images_save
                write_output(script_filename, images_repeats, images_save)
        elif len(event.char) == 1:
            if event.char == '\r':
                self.msg = f'Return {self.nums}'
                if self.index == -1:
                    self.show_next()
                    return
                if len(self.nums) == 0:
                    return
                self.output(self.nums)
                self.nums = set()
                show_next = True
        else:
            if event.keysym == 'Left':
                self.show_prev()
                return
            elif event.keysym == 'Right':
                self.show_next()
                return
        self.label1.config(text=self.msg)
        if show_next:
            self.show_next()


root = Tk()
app = Window(root)
root.wm_title('Duplicate image remove assistant')
root.geometry('1280x800')

root.mainloop()

print('Exit')
