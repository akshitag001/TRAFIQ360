import sys
import os

print("Step 1: basic imports complete", flush=True)
sys.path.append(r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360")
sys.path.append(r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360\scratch")
sys.path.append(r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360\services")

print("Step 2: importing joblib...", flush=True)
import joblib
print("Step 3: importing pandas...", flush=True)
import pandas as pd
print("Step 4: importing networkx...", flush=True)
import networkx as nx

print("Step 5: importing gis_twin...", flush=True)
import gis_twin
print("Step 6: importing server...", flush=True)
import server
print("Step 7: success!", flush=True)
