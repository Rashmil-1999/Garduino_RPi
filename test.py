from datetime import datetime as dt
import os

dire = os.getcwd()

with open(os.path.join(dire, "test.txt"), "a") as f:
    print(dt.now().strftime("%H:%M:%S"))
    f.write(str(dt.now().strftime("%H:%M:%S\n")))