import os
import random
import sys
import sys
from datetime import datetime
from faker import Faker
faker = Faker()

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import replicate_files
from utils import get_claims, get_bene, get_prov
from utils import pcs

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

# Prepare data structures for lookups.
claims = get_claims("A")
claims_count = len(claims)

# Enumerate over the claims and emit to a temporary file.
file_name = "CCLF3.txt"
with open(f"{directory}/{file_name}", "w") as f:
    # Enumerate over the claims.
    for index, claim in enumerate(claims):

        # Output a status message.
        if(index == 0 or index + 1 == claims_count or index % 1000 == 0):
            print(f"CCLF3 Processing for {file_date}: {int(100 * ((1 + index) / claims_count))}%", end="\r")
        
        # Get the beneficiary and NPI provider.
        line = ""
        bene = get_bene(claim["mbi"])
        prov = get_prov(claim["npi"])
        proc = random.choice(pcs(claim["icd_ver"]))

        # 1-10
        line += claim["num"].ljust(13)          # CUR_CLM_UNIQ_ID
        line += claim["mbi"]                    # BENE_MBI_ID
        line += "".ljust(11)                    # BENE_HIC_NUM
        line += claim["ctc"]                    # CLM_TYPE_CD
        line += "01"                            # CLM_VAL_SQNC_NUM
        line += proc["code"].rjust(7)           # CLM_PRCDR_CD
        line += claim["from_dt"]                # CLM_PRCDR_PRFRM_DT
        line += "".ljust(11)                    # BENE_EQTBL_BIC_HICN_NUM
        line += prov["oscar"].ljust(6)          # PRVDR_OSCAR_NUM
        line += claim["from_dt"]                # CLM_FROM_DT

        # 11-13
        line += claim["thru_dt"]                # CLM_THRU_DT   
        line += proc["ver"]                     # DGNS_PRCDR_ICD_IND
        line += prov["oscar"].rjust(20)         # CLM_BLG_PRVDR_OSCAR_NUM
        line += "\n"

        f.write(line)  
    
    print("")

print(f"CCLF3 Processing for {file_date}: Complete")
replicate_files("CCLF3", file_date)    
  