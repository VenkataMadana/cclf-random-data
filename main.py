import argparse
import datetime
import os
import random
import subprocess
import sys

sys.path.append("./utils/")
from utils import purge_output_folder, seed_random, write_summary_files
from caches import cache_all


# Specifies the total population size of beneficiaries that can be randomly
# chosen and used to generate files.
number_of_beneficiaries = 1000

# Specifies the total population size of providers that can be randomly
# chosen and used to generate files.
number_of_providers = 2000

# Specifies the number of claims that will be generated and in which month
# and year.
number_of_claims = 10000
claims_year = 2024
claims_month = 8

parser = argparse.ArgumentParser(description="Generate fake CCLF files.")
parser.add_argument("--seed", type=int, help="repeat an earlier run by reusing its seed")
parser.add_argument("--beneficiaries", type=int, default=number_of_beneficiaries)
parser.add_argument("--providers", type=int, default=number_of_providers)
parser.add_argument("--claims", type=int, default=number_of_claims)
args = parser.parse_args()

# Every run has a seed, and it is printed so that the run can be repeated.
seed = args.seed if args.seed is not None else random.randrange(2**32)
print(f"Seed: {seed}")
seed_random(seed)

# Clean up date from previous runs.
purge_output_folder()

# Prepare the caches.
cache_all(args.beneficiaries, args.providers, args.claims, claims_year, claims_month)

# Specifies the scripts that will be called each time main is executed.
scripts = [
    "./cclf_1.py", 
    "./cclf_2.py", 
    "./cclf_3.py", 
    "./cclf_4.py", 
    "./cclf_5.py", 
    "./cclf_6.py", 
    "./cclf_7.py", 
    "./cclf_8.py", 
    "./cclf_9.py", 
    "./cclf_a.py",
    "./cclf_b.py",
]

# Files are dated the first of the month after the claims.
next_month = datetime.date(claims_year, claims_month, 28) + datetime.timedelta(days=4)
file_dt = next_month.replace(day=1).strftime("%Y-%m-%d")

# Convert the arguments to strins.
script_args = [str(file_dt)]

# Stop at the first script that fails.
env = {**os.environ, "CCLF_SEED": str(seed)}
for script in scripts:
    subprocess.run([sys.executable, script] + script_args, check=True, env=env)

write_summary_files(file_dt)
