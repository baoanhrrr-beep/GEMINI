"""
Firebase Panel Finder - tim panel moi co du lieu Jio SMS
Thu cac ten Firebase pho bien tu cong dong tool An Do
"""
import requests
import concurrent.futures
from datetime import datetime

NAMES = [
    # Tool keywords
    "jiopanel", "jiogem", "jiomaster", "jiomain", "jiobot",
    "gemmaster", "gempanel", "gembot", "gemactivate",
    "masterbot", "masterpanel", "mainpanel", "mainbot",
    "otpmaster", "otppanel", "otpbot", "otpreader",
    "smspanel", "smsbot", "smsmaster", "smsreader",
    "activator", "activation", "activepanel",
    "indiabot", "indiapanel", "indiamaster",
    "jioactivation", "jiootp", "jiolink",
    "mypanel", "mybot", "mymaster",
    "freegem", "freegoogle", "gemfree",
    "googleai", "googleone", "googlegem",
    "rechargepanel", "rechargebot",
    "autobot", "automaster", "autopanel",
    "kingpanel", "kingbot", "kingmaster",
    "bossbot", "bosspanel", "bossmaster",
    "superbot", "superpanel", "supermaster",
    "viralpanel", "viral", "viralbot",
    "fastpanel", "fastbot", "quickpanel", "quickbot",
    "smartpanel", "smartbot", "vippanel", "vipbot",
    "prempanel", "prembot", "goldpanel", "goldbot",
    "royalpanel", "royalbot", "maxpanel", "maxbot",
    "megapanel", "megabot", "ultrapanel", "ultrabot",
    "turbopanel", "turbobot", "flashpanel", "flashbot",
    "rapidpanel", "rapidbot", "probot", "propanel",
    "elitepanel", "elitebot", "premiumpanel", "premiumbot",
    "hackpanel", "freepanel", "newpanel", "newbot",
    # Numbers
    "panel1", "panel2", "panel3", "panel4", "panel5",
    "panel6", "panel7", "panel8", "panel9", "panel10",
    "jio1", "jio2", "jio3", "jio4", "jio5",
    "jio6", "jio7", "jio8", "jio9", "jio10",
    "jio11", "jio12", "jio13", "jio14", "jio15",
    "gem1", "gem2", "gem3", "gem4", "gem5",
    "otp1", "otp2", "otp3", "otp4", "otp5",
    "sms1", "sms2", "sms3", "sms4", "sms5",
    "tool1", "tool2", "tool3", "tool4", "tool5",
    "free1", "free2", "free3", "free4", "free5",
    "new1", "new2", "new3", "new4", "new5",
    "hack1", "hack2", "hack3",
    "test1", "test2", "test3",
    "india1", "india2", "india3", "india4", "india5",
    "bot1", "bot2", "bot3", "bot4", "bot5",
    # Indian male names
    "rupesh", "santosh", "rajesh", "suresh", "ramesh",
    "vikash", "vikram", "rahul", "rohit", "ravi",
    "amit", "sanjay", "mahesh", "naresh", "dinesh",
    "ganesh", "umesh", "aakash", "akash", "deepak",
    "pradeep", "manish", "anil", "arvind", "kamal",
    "pankaj", "nitin", "aman", "ankit", "vishal",
    "sachin", "rohan", "mohit", "prince", "lucky",
    "sunny", "rinku", "bunty", "pappu", "bablu",
    "tinku", "chotu", "pintu", "guddu", "munna",
    "raju", "raja", "shyam", "gopal", "mohan",
    "sohan", "roshan", "krishan", "balram", "arjun",
    "abhishek", "shubham", "himanshu", "harish",
    "rakesh", "lokesh", "mukesh", "ritesh", "devesh",
    "yogesh", "shivam", "shiva", "kumar", "karan",
    "kartik", "kapil", "varun", "tarun", "arun",
    "chandan", "ranjan", "sajan", "madan", "pavan",
    "ranjit", "gurjit", "amrit", "dilip", "sunil",
    "sharma", "verma", "gupta", "singh", "yadav",
    "pandey", "tiwari", "mishra", "shukla", "dubey",
    "chauhan", "rajput", "thakur", "jha", "sinha",
    "nair", "menon", "iyer", "reddy", "rao",
    "naidu", "babu", "patil", "das", "roy",
    # Indian female names
    "priya", "pooja", "neha", "anita", "sunita",
    "kavita", "geeta", "seeta", "reeta", "annu",
    "rani", "shilpa", "simran", "sapna", "rekha",
    "meera", "komal", "sonal", "kiran", "nisha",
    "disha", "usha", "asha", "lata", "maya",
    "radha", "sita", "gita", "mita", "rita",
    "hema", "prema", "saroj", "laxmi", "durga",
    "parvati", "gauri", "kamla", "vidya", "vimal",
    # Cities
    "delhi", "mumbai", "kolkata", "chennai", "bangalore",
    "hyderabad", "pune", "jaipur", "lucknow", "patna",
    "bhopal", "nagpur", "surat", "ahmedabad", "chandigarh",
    "up", "bihar", "mp", "raj", "guj",
    "haryana", "punjab", "kerala", "odisha", "assam",
    # Combo keywords
    "jiorecharge", "jiocare", "jiohelp", "jiosupport",
    "jioservice", "jioshare", "jiofree", "jiogift",
    "jiobonus", "jiooffer", "jiodeal", "jiopromo",
    "gemshare", "gemgift", "gemlink", "gemtool",
    "otpshare", "otpget", "otpfetch", "otpread",
    "smsget", "smsfetch", "smsread", "smsforward",
    "activation1", "activation2", "activation3",
    "active1", "active2", "active3",
    "recharge1", "recharge2", "recharge3",
    "offer1", "offer2", "offer3",
]

SUFFIXES = ["", "-1", "-2", "-3", "-4", "-5", "-v2", "-v3", "-new", "-main", "-master", "-bot", "-panel", "-jio", "-otp"]

TIMEOUT = 8
FOUND_FILE = "new_panels_found.txt"

def check_panel(url: str) -> tuple:
    try:
        r = requests.get(f"{url}/clients.json", timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and len(data) > 0:
                online = sum(1 for v in data.values() if isinstance(v, dict) and v.get("status") is True)
                return url, True, online
        return url, False, r.status_code
    except Exception:
        return url, False, -1

def main():
    urls = []
    seen = set()
    for name in NAMES:
        for suffix in SUFFIXES:
            full = f"{name}{suffix}"
            url = f"https://{full}-default-rtdb.firebaseio.com"
            if url not in seen:
                seen.add(url)
                urls.append(url)

    print(f"Checking {len(urls)} potential Firebase panels...")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}\n")

    found = []
    checked = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        futures = {executor.submit(check_panel, url): url for url in urls}
        for future in concurrent.futures.as_completed(futures):
            url, success, info = future.result()
            checked += 1
            if success:
                online_count = info
                print(f"[FOUND] {url} -> {online_count} devices online")
                found.append(url)
                with open(FOUND_FILE, "a", encoding="utf-8") as f:
                    f.write(f"{url}\n")
            elif checked % 100 == 0:
                print(f"  Checked {checked}/{len(urls)}...")

    print(f"\n{'='*60}")
    print(f"DONE - Found {len(found)} live panels out of {len(urls)} checked")
    print(f"Saved to: {FOUND_FILE}")
    for f in found:
        print(f"  {f}")

if __name__ == "__main__":
    main()
