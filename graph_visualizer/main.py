# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----- notes
# ----------------------------------------------------------------------------------------
"""
pip install seaborn





"""
# ----------------------------------------------------------------------------------------
# ----- libraries
# ----------------------------------------------------------------------------------------
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

import time
import math

# ----------------------------------------------------------------------------------------
# ----- functions
# ----------------------------------------------------------------------------------------
def scale_value(value, input_min, input_max, output_min, output_max):
    # Scale the value from the input range to the output range
    scaled_value = ((value - input_min) / (input_max - input_min)) \
        * (output_max - output_min) + output_min
    return scaled_value


# ----------------------------------------------------------------------------------------
# ----- main
# ----------------------------------------------------------------------------------------
def blackboard():
    # Example hex color code
    max_val = 0.0
    graph_x =  []
    graph_y =  []
    
    difference = -1
    time_pin = time.time()
    time_print_delay = time_pin
    
    waiting_delay = 1
    
    glfw_time_limit = time.time() + 20
    
    mod = "waiting0"
    
    while time.time() < glfw_time_limit:
        value = 0.0
        if mod == "waiting0":
            value = 0.0
            if time.time() > time_pin + waiting_delay:
                difference  = time.time() - time_pin
                mod = "expand"
                
        elif mod == "expand":
            value = abs(math.tan(time.time()-difference))
            if value > 2000:
                value = 2000
                time_pin = time.time()
                mod = "waiting1"
                
        elif mod == "waiting1":
            value = 2000
            if time.time() > time_pin + waiting_delay:
                difference  = time.time() - time_pin
                mod = "collapse"
                
        elif mod == "collapse":
            value = abs(math.tan(time.time()-difference))
            if value < 0.1:
                value = 0.0
                time_pin = time.time()
                mod = "waiting0"

        if time.time() > time_print_delay + .1:
            time_print_delay = time.time()
            formatted_value = "{:.{}f}".format(value, 4)
            print(formatted_value, int(time.time()))
        # print(value, time.time())
            graph_x.append(time.time())
            graph_y.append(value)
    
    
    draw2(graph_x, graph_y)


def draw(x, y):
    sns.set_theme(style="whitegrid")
    rs = np.random.RandomState(365)
    values = rs.randn(365, 4).cumsum(axis=0)
    dates = pd.date_range("1 1 2016", periods=365, freq="D")
    data = pd.DataFrame(x, y)
    data = data.rolling(7).mean()

    sns.lineplot(data=data, palette="tab10", linewidth=2.5)
    plot.show()
    
def draw2(x, y):
    # Example arrays
    # x = [1, 2, 3, 4, 5]
    # y1 = [2, 3, 5, 7, 11]
    # y2 = [1, 4, 9, 16, 25]

    # Plotting both arrays
    plt.plot(x, y, label='time - value')

    # Adding labels and title
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    # plt.title('Plotting Two Arrays')


    # Displaying the plot
    plt.show()

# ----------------------------------------------------------------------------------------
# ----- start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    blackboard()