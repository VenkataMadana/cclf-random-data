import os
import random
import sys
import sys
from datetime import datetime
from faker import Faker
faker = Faker()

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import dol, replicate_files
from utils import get_claims, get_bene, get_prov
from utils import revcd, hcpcs, flt, hcpcsm, hipps

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
file_name = "CCLF2.txt"
with open(f"{directory}/{file_name}", "w") as f:
    # Enumerate over the claims.
    for index, claim in enumerate(claims):

        # Output a status message.
        if(index == 0 or index + 1 == claims_count or index % 1000 == 0):
            print(f"CCLF2 Processing for {file_date}: {int(100 * ((1 + index) / claims_count))}%", end="\r")

        # Enumerate the claim lines.
        for claim_line in claim["lines"]:

            # Get the beneficiary and NPI provider.
            line = ""
            bene = get_bene(claim["mbi"])
            prov = get_prov(claim["npi"])

            # 1-10
            line += claim["num"].ljust(13)              # CUR_CLM_UNIQ_ID
            line += claim_line["ln"].zfill(10)          # CLM_LINE_NUM
            line += claim["mbi"]                        # BENE_MBI_ID
            line += "".ljust(11)                        # BENE_HIC_NUM
            line += claim["ctc"]                    # CLM_TYPE_CD
            line += claim_line["from_dt"]               # CLM_LINE_FROM_DT
            line += claim_line["thru_dt"]               # CLM_LINE_THRU_DT
            line += random.choice(revcd()).rjust(4)     # CLM_LINE_PROD_REV_CTR_CD
            line += claim_line["thru_dt"]               # CLM_LINE_INSTNL_REV_CTR_DT   
            line += random.choice(hcpcs())              # CLM_LINE_HCPCS_CD
    
            # 11-20
            line += "".ljust(11)                        # BENE_EQTBL_BIC_HICN_NUM
            line += prov["oscar"].ljust(6)              # PRVDR_OSCAR_NUM
            line += claim["from_dt"]                    # CLM_FROM_DT
            line += claim["thru_dt"]                    # CLM_THRU_DT       
            line += flt().rjust(24)                     # CLM_LINE_SRVC_UNIT_QTY
            line += dol().rjust(17)                     # CLM_LINE_CVRD_PD_AMT
            line += random.choice(hcpcsm())             # HCPCS_1_MDFR_CD
            line += random.choice(hcpcsm())             # HCPCS_2_MDFR_CD
            line += random.choice(hcpcsm())             # HCPCS_3_MDFR_CD
            line += random.choice(hcpcsm())             # HCPCS_4_MDFR_CD

            # 21-23
            line += random.choice(hcpcsm())             # HCPCS_5_MDFR_CD
            line += random.choice(hipps()).rjust(5)     # CLM_REV_APC_HIPPS_CD
            line += prov["oscar"].rjust(20)             # CLM_FAC_PRVDR_OSCAR_NUM

            line += "\n"

            f.write(line)  
    

print(f"CCLF2 Processing for {file_date}: Complete")
replicate_files("CCLF2", file_date)    