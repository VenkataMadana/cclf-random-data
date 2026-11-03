import os
import random
import sys
import sys
from datetime import datetime, timedelta
from faker import Faker
faker = Faker()

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import replicate_files, dol
from utils import get_claims, get_bene, get_prov
from utils import ynb, twobyte, hpsa

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
claims = get_claims("B")
claims_count = len(claims)

# Enumerate over the claims and emit to a temporary file.
file_name = "CCLFB.txt"
with open(f"{directory}/{file_name}", "w") as f:
    # Enumerate over the claims.
    for index, claim in enumerate(claims):

        # Output a status message.
        if(index == 0 or index + 1 == claims_count or index % 1000 == 0):
            print(f"CCLFB Processing for {file_date}: {int(100 * ((1 + index) / claims_count))}%", end="\r")     

        # Enumerate the claim lines.
        for claim_line in claim["lines"]:

            # Get the beneficiary and NPI provider.
            line = ""
            bene = get_bene(claim["mbi"])
            prov = get_prov(claim["npi"])
            
            # 1-10
            line += claim["num"].ljust(13)          # CUR_CLM_UNIQ_ID
            line += claim_line["ln"].zfill(10)      # CLM_LINE_NUM
            line += bene["mbi"]                     # BENE_MBI_ID
            line += bene["hic"].ljust(11)           # BENE_HIC_NUM
            line += claim["ctc"]                    # CLM_TYPE_CD
            line += ynb()                           # CLM_LINE_NGACO_PBPMT_SW
            line += ynb()                           # CLM_LINE_NGACO_PDSCHRG_HCBS_SW
            line += ynb()                           # CLM_LINE_NGACO_SNF_WVR_SW
            line += ynb()                           # CLM_LINE_NGACO_TLHLTH_SW
            line += ynb()                           # CLM_LINE_NGACO_CPTATN_SW

            # 11-20
            line += twobyte()                       # CLM_DEMO_1ST_NUM
            line += twobyte()                       # CLM_DEMO_2ND_NUM
            line += twobyte()                       # CLM_DEMO_3RD_NUM
            line += twobyte()                       # CLM_DEMO_4TH_NUM
            line += twobyte()                       # CLM_DEMO_5TH_NUM
            line += dol().rjust(15)                 # CLM_PBP_INCLSN_AMT
            line += dol().rjust(15)                 # CLM_PBP_RDCTN_AMT
            line += ynb()                           # CLM_NGACO_CMG_WVR_SW
            line += dol().rjust(19)                 # CLM_MDCR_DDCTBL_AMT
            line += dol().rjust(15)                 # CLM_SQSTRTN_RDCTN_AMT

            # 21
            line += random.choice(hpsa())           # CLM_LINE_CARR_HPSA_SCRCTY_CD

            line += "\n"

            f.write(line)  
    
print(f"CCLFB Processing for {file_date}: Complete")
replicate_files("CCLFB", file_date)        