import tkinter

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# implement the default Matplotlib key bindings
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np
import json

data_entries = []
time_entries = []
with open('data.json', 'r') as f:
    for item in f:
        data = item.("CPU Core #2")
        time = item.("Time")


root = tkinter.Tk()  # tkinter base window
root.wm_title("Embedding in Tk")  # window title

fig = Figure(figsize=(5, 4), dpi=100)  # create new figure, figsize = width & height(inches), dpi = resolution - default
t = np.arange(0, 3, 0.1)  # returns evenly spaced values in ndarray format, args: start, stop, step, dtype
fig.add_subplot(111).plot(time, data)  # add axes to the figure as part of a subplot arrangement
# 3-digits: nrows, ncols and index in order, defaults to 111
# .plot plot x versus y, x and y can be list with equal indexes giving coordinates

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()


def on_key_press(event):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)


canvas.mpl_connect("key_press_event", on_key_press)
button = tkinter.Button(master=root, text="Quit", command=root.quit)

# Packing order is important. Widgets are processed sequentially and if there
# is no space left, because the window is too small, they are not displayed.
# The canvas is rather flexible in its size, so we pack it last which makes
# sure the UI controls are displayed as long as possible.

button.pack(side=tkinter.BOTTOM)  # puts buttons below graph
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

tkinter.mainloop()  # to run the GUI
