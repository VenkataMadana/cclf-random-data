import os
import sys
import sys
from datetime import datetime
from faker import Faker
faker = Faker()

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import replicate_files
from utils import get_beneficiaries

# Define the path for the files.
directory = f"./_output/cache"
if not os.path.exists(directory):
    os.makedirs(directory, exist_ok=True)

# Capture arguments or default if not provided.
if len(sys.argv) == 2:
    # Capture arguments and convert them
    try:
        file_date = sys.argv[1]
    except ValueError as e:
        sys.exit(1)  # Exit with error code    
else:
    file_date = datetime.now().strftime("%Y-%m-%d")

# Prepare data structures for lookups. Only beneficiaries with an MBI change
# appear in this file.
beneficiaries = [bene for bene in get_beneficiaries().values() if bene["prev_mbi"]]
beneficiaries_count = len(beneficiaries)

# Enumerate over the beneficiaries and emit to a temporary file.
file_name = "CCLF9.txt"
with open(f"{directory}/{file_name}", "w") as f:

    # Enumerate over the claims.
    for index, bene in enumerate(beneficiaries):    

        # Output a status message.
        if(index == 0 or index + 1 == beneficiaries_count or index % 1000 == 0):
            print(f"CCLF9 Processing for {file_date}: {int(100 * ((1 + index) / beneficiaries_count))}%", end="\r")       

        # Initialize.
        line = ""

        # 1-6
        line += "M"                     # HICN_MBI_XREF_IND
        line += bene["mbi"]             # CRNT_NUM
        line += bene["prev_mbi"]        # PRVS_NUM
        line += bene["prev_mbi_efctv"]  # PRVS_ID_EFCTV_DT
        line += bene["prev_mbi_obslt"]  # PRVS_ID_OBSLT_DT
        line += "".ljust(12)            # BENE_RRB_NUM

        line += "\n"

        f.write(line)  
    
print(f"CCLF9 Processing for {file_date}: Complete")
replicate_files("CCLF9", file_date)             
  