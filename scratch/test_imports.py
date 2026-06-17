import platform
from collections import namedtuple
UnameResult = namedtuple('uname_result', ['system', 'node', 'release', 'version', 'machine'])
platform.win32_ver = lambda release='', version='', csd='', ptype='': ('10', '10.0.19045', '', 'Multiprocessor Free')
platform.uname = lambda: UnameResult('Windows', 'DESKTOP', '10', '10.0.19045', 'AMD64')

import sys
print("networkx...", end="", flush=True)
import networkx as nx
print("ok\npulp...", end="", flush=True)
import pulp
print("ok\nshapely...", end="", flush=True)
from shapely import wkt
print("ok\nfolium...", end="", flush=True)
import folium
print("ok\nselenium...", end="", flush=True)
from selenium import webdriver
print("ok\nselenium chrome options...", end="", flush=True)
from selenium.webdriver.chrome.options import Options
print("ok\nreportlab...", end="", flush=True)
from reportlab.lib.pagesizes import letter
print("ok\nAll imported!", flush=True)
