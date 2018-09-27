import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Data for plotting
t = [1,2,3]
s = [3,2,3]
fig, ax = plt.subplots()
ax.plot(t, s)

ax.set(xlabel='time (s)', ylabel='voltage (mV)',
       title='About as simple as it gets, folks')
ax.grid()

fig.savefig("test.png")
plt.show()

