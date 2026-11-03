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
from utils import cdsc, ndc, psiqc, daw, flt, rint, cat, pstc

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
claims = get_claims("D")
claims_count = len(claims)

# Enumerate over the claims and emit to a temporary file.
file_name = "CCLF7.txt"
with open(f"{directory}/{file_name}", "w") as f:
    # Enumerate over the claims.
    for index, claim in enumerate(claims):

        # Output a status message.
        if(index == 0 or index + 1 == claims_count or index % 1000 == 0):
            print(f"CCLF7 Processing for {file_date}: {int(100 * ((1 + index) / claims_count))}%", end="\r")     

        # Initialize.
        line = ""
        bene = get_bene(claim["mbi"])
        prov = get_prov(claim["npi"])

        # 1-10
        line += claim["num"].ljust(13)          # CUR_CLM_UNIQ_ID
        line += claim["mbi"]                    # BENE_MBI_ID
        line += "".ljust(11)                    # BENE_HIC_NUM
        line += ndc()                           # CLM_LINE_NDC_CD
        line += claim["ctc"]                    # CLM_TYPE_CD
        line += claim["from_dt"]                # CLM_LINE_FROM_DT
        line += random.choice(psiqc())          # PRVDR_SRVC_ID__QLFYR_CD
        line += prov["npi"].ljust(20)           # CLM_SRVC_PRVDR_GNRC_ID_NUM
        line += random.choice(cdsc())           # CLM_DSPNSNG_STUS_CD
        line += random.choice(daw())            # CLM_DAW_PROD_SLCTN_CD
        
        # 11-20
        line += flt().rjust(24)                 # CLM_LINE_SRVC_UNIT_QTY
        line += rint().zfill(9)                 # CLM_LINE_DAYS_SUPLY_QTY
        line += random.choice(psiqc())          # PRVDR_PRSBNG_ID_QLFYR_CD
        line += prov["npi"].ljust(20)           # CLM_PRSBNG_PRVDR_GNRC_ID_NUM
        line += dol().rjust(13)                 # CLM_LINE_BENE_PMT_AMT
        line += random.choice(cat()).ljust(2)   # CLM_ADJSMT_TYPE_CD
        line += claim["from_dt"]                # CLM_EFCTV_DT
        line += claim["thru_dt"]                # CLM_IDR_LD_DT
        line += rint().zfill(12)                # CLM_LINE_RX_SRVC_RFRNC_NUM  
        line += rint().rjust(9)                 # CLM_LINE_RX_FILL_NUM

        # 21
        line += random.choice(pstc()).ljust(2)  # CLM_PHRMCY_SRVC_TYPE_CD

        line += "\n"

        f.write(line)  
    
print(f"CCLF7 Processing for {file_date}: Complete")
replicate_files("CCLF7", file_date)     