import skfuzzy as fz
from skfuzzy import control as ctrl
import numpy as np
import matplotlib.pyplot as plt
import time

dirt = ctrl.Antecedent(np.arange(0, 200, 1), "dirt")
grease = ctrl.Antecedent(np.arange(0, 200, 1), "grease")
washtime = ctrl.Consequent(np.arange(0, 60, 1), "time")
washtime.defuzzify_method = "mom"

# # Generate universe variables
# #   * soil moisture, soil temperature, air moisture, air temperature on subjective ranges [0, 100]
# #   * water time has a range of [0, 100] in units of seconds
# x_smois = np.arange(0, 101, 1)
# x_stemp = np.arange(0, 101, 1)
# x_amois = np.arange(0, 101, 1)
# x_atemp = np.arange(0, 101, 1)
# x_water = np.arange(0, 100, 1)

# # Generate fuzzy membership functions
# smois_vlow = fz.trimf(x_smois, [0, 0, 25])
# smois_low = fz.trimf(x_smois, [0, 25, 50])
# smois_med = fz.trimf(x_smois, [25, 50, 75])
# smois_high = fz.trimf(x_smois, [50, 75, 100])
# smois_vhigh = fz.trimf(x_smois, [75, 100, 100])

# stemp_vlow = fz.trimf(x_stemp, [0, 0, 25])
# stemp_low = fz.trimf(x_stemp, [0, 25, 50])
# stemp_med = fz.trimf(x_stemp, [25, 50, 75])
# stemp_high = fz.trimf(x_stemp, [50, 75, 100])
# stemp_vhigh = fz.trimf(x_stemp, [75, 100, 100])

# amois_vlow = fz.trimf(x_amois, [0, 0, 25])
# amois_low = fz.trimf(x_amois, [0, 25, 50])
# amois_med = fz.trimf(x_amois, [25, 50, 75])
# amois_high = fz.trimf(x_amois, [50, 75, 100])
# amois_vhigh = fz.trimf(x_amois, [75, 100, 100])

# atemp_vlow = fz.trimf(x_atemp, [0, 0, 25])
# atemp_low = fz.trimf(x_atemp, [0, 25, 50])
# atemp_med = fz.trimf(x_atemp, [25, 50, 75])
# atemp_high = fz.trimf(x_atemp, [50, 75, 100])
# atemp_vhigh = fz.trimf(x_atemp, [75, 100, 100])

# # Visualize these universes and membership functions
# fig, (ax0, ax1, ax2, ax3) = plt.subplots(nrows=4, figsize=(8, 9))

# ax0.plot(x_smois, smois_vlow, "b", linewidth=1.5, label="Very Low")
# ax0.plot(x_smois, smois_low, "g", linewidth=1.5, label="Low")
# ax0.plot(x_smois, smois_med, "r", linewidth=1.5, label="Medium")
# ax0.plot(x_smois, smois_high, "y", linewidth=1.5, label="High")
# ax0.plot(x_smois, smois_vhigh, "o", linewidth=1.5, label="Very High")
# ax0.set_title("Soil Moisture")
# ax0.legend()

# ax1.plot(x_stemp, stemp_vlow, "b", linewidth=1.5, label="Very Low")
# ax1.plot(x_stemp, stemp_low, "g", linewidth=1.5, label="Low")
# ax1.plot(x_stemp, stemp_med, "r", linewidth=1.5, label="Medium")
# ax1.plot(x_stemp, stemp_high, "y", linewidth=1.5, label="High")
# ax1.plot(x_stemp, stemp_vhigh, "o", linewidth=1.5, label="Very High")
# ax1.set_title("Soil Temperature")
# ax1.legend()

# ax2.plot(x_amois, amois_vlow, "b", linewidth=1.5, label="Very Low")
# ax2.plot(x_amois, amois_low, "g", linewidth=1.5, label="Low")
# ax2.plot(x_amois, amois_med, "r", linewidth=1.5, label="Medium")
# ax2.plot(x_amois, amois_high, "y", linewidth=1.5, label="High")
# ax2.plot(x_amois, amois_vhigh, "o", linewidth=1.5, label="Very High")
# ax2.set_title("Air Humidity")
# ax2.legend()

# ax3.plot(x_atemp, atemp_vlow, "b", linewidth=1.5, label="Very Low")
# ax3.plot(x_atemp, atemp_low, "g", linewidth=1.5, label="Low")
# ax3.plot(x_atemp, atemp_med, "r", linewidth=1.5, label="Medium")
# ax3.plot(x_atemp, atemp_high, "y", linewidth=1.5, label="High")
# ax3.plot(x_atemp, atemp_vhigh, "o", linewidth=1.5, label="Very High")
# ax3.set_title("Air Temperature")
# ax3.legend()

# # Turn off top/right axes
# for ax in (ax0, ax1, ax2, ax3):
#     ax.spines["top"].set_visible(False)
#     ax.spines["right"].set_visible(False)
#     ax.get_xaxis().tick_bottom()
#     ax.get_yaxis().tick_left()

# plt.tight_layout()
# plt.show()

# fig, (ax0, ax1) = plt.subplots(nrows=2, figsize=(8, 9))

# ax0.plot([[i for i in range(200)]], dirt["sd"], "b", linewidth=1.5, label="Small Dirt")
# ax0.plot([[i for i in range(200)]], dirt["md"], "g", linewidth=1.5, label="Medium Dirt")
# ax0.plot([[i for i in range(200)]], dirt["ld"], "r", linewidth=1.5, label="Large Dirt")
# ax0.set_title("Dirt")
# ax0.legend()

# ax1.plot(
#     [[i for i in range(200)]], grease["sg"], "b", linewidth=1.5, label="Small Grease"
# )
# ax1.plot(
#     [[i for i in range(200)]], grease["mg"], "g", linewidth=1.5, label="Medium Grease"
# )
# ax1.plot(
#     [[i for i in range(200)]], grease["lg"], "r", linewidth=1.5, label="Large Grease"
# )
# ax1.set_title("Service quality")
# ax1.legend()

# rule1 = ctrl.Rule(dirt["sd"] & grease["sg"], washtime["vs"])
# rule2 = ctrl.Rule(dirt["sd"] & grease["mg"], washtime["m"])
# rule3 = ctrl.Rule(dirt["sd"] & grease["lg"], washtime["l"])
# rule4 = ctrl.Rule(dirt["md"] & grease["sg"], washtime["s"])
# rule5 = ctrl.Rule(dirt["md"] & grease["mg"], washtime["m"])
# rule6 = ctrl.Rule(dirt["md"] & grease["lg"], washtime["l"])
# rule7 = ctrl.Rule(dirt["ld"] & grease["sg"], washtime["m"])
# rule8 = ctrl.Rule(dirt["ld"] & grease["mg"], washtime["l"])
# rule9 = ctrl.Rule(dirt["ld"] & grease["lg"], washtime["vl"])

# wash_ctrl = ctrl.ControlSystem(
#     [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9]
# )
# machine = ctrl.ControlSystemSimulation(wash_ctrl)
# machine.input["dirt"], machine.input["grease"] = 110, 170
# machine.compute()
# plt.show()
# print("wash time is {}".format(machine.output["time"]))
