import matplotlib.pyplot as plt
import matplotlib.animation as animation

from utils import AccelerometerStream

###
# Global Variables
###

FIG = plt.figure()
AXES = FIG.add_subplot(1,1,1)
X_VALS = []
Y_VALS = []
time = 0

###
# Helpers
###

def animate(i):
    if NiosStream.events.is_set():
        data = NiosStream.get()
        X_VALS.append(i)
        Y_VALS.append(data)
        AXES.clear()
        AXES.plot(X_VALS, Y_VALS)

###
# Main
###

if __name__ == "__main__":
    NiosStream = AccelerometerStream()
    ani = animation.FuncAnimation(FIG, animate, interval=10)
    plt.show()