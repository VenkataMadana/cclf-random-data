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
from utils import get_claims
from utils import ynb, twobyte, crc, ansi_reason, ansi_group

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
file_name = "CCLFA.txt"
with open(f"{directory}/{file_name}", "w") as f:
    # Enumerate over the claims.
    for index, claim in enumerate(claims):

        # Output a status message.
        if(index == 0 or index + 1 == claims_count or index % 1000 == 0):
            print(f"CCLFA Processing for {file_date}: {int(100 * ((1 + index) / claims_count))}%", end="\r")     

        # Initialize.
        line = ""

        # 1-10
        line += claim["num"].ljust(13)          # CUR_CLM_UNIQ_ID
        line += claim["mbi"]                    # BENE_MBI_ID
        line += "".ljust(11)                    # BENE_HIC_NUM
        line += claim["ctc"]                    # CLM_TYPE_CD
        line += claim["from_dt"]                # CLM_ACTV_CARE_FROM_DT
        line += ynb()                           # CLM_NGACO_PBPMT_SW
        line += ynb()                           # CLM_NGACO_PDSCHRG_HCBS_SW
        line += ynb()                           # CLM_NGACO_SNF_WVR_SW
        line += ynb()                           # CLM_NGACO_TLHLTH_SW
        line += ynb()                           # CLM_NGACO_CPTATN_SW

        # 11-20
        line += twobyte()                       # CLM_DEMO_1ST_NUM
        line += twobyte()                       # CLM_DEMO_2ND_NUM
        line += twobyte()                       # CLM_DEMO_3RD_NUM
        line += twobyte()                       # CLM_DEMO_4TH_NUM
        line += twobyte()                       # CLM_DEMO_5TH_NUM
        line += dol().rjust(19)                 # CLM_PBP_INCLSN_AMT
        line += dol().rjust(19)                 # CLM_PBP_RDCTN_AMT
        line += ynb()                           # CLM_NGACO_CMG_WVR_SW
        line += dol().rjust(19)                 # CLM_INSTNL_PER_DIEM_AMT
        line += dol().rjust(15)                 # CLM_MDCR_IP_BENE_DDCTBL_AMT

        # 21-30
        line += dol().rjust(19)                 # CLM_MDCR_COINSRNC_AMT
        line += dol().rjust(15)                 # CLM_BLOOD_LBLTY_AMT
        line += dol().rjust(15)                 # CLM_INSTNL_PRFNL_AMT
        line += dol().rjust(19)                 # CLM_NCVRD_CHRG_AMT
        line += dol().rjust(19)                 # CLM_MDCR_DDCTBL_AMT
        line += random.choice(crc())            # CLM_RLT_COND_CD
        line += dol().rjust(19)                 # CLM_OPRTNL_OUTLR_AMT
        line += dol().rjust(19)                 # CLM_MDCR_NEW_TECH_AMT
        line += dol().rjust(19)                 # CLM_ISLET_ISOLN_AMT
        line += dol().rjust(19)                 # CLM_SQSTRTN_RDCTN_AMT

        # 31-33
        line += random.choice(ansi_reason()).ljust(3) # CLM_1_REV_CNTR_ANSI_RSN_CD       
        line += random.choice(ansi_group())     # CLM_1_REV_CNTR_ANSI_GRP_CD
        line += dol().rjust(19)                 # CLM_MIPS_PMT_AMT

        line += "\n"

        f.write(line)  
    
print(f"CCLFA Processing for {file_date}: Complete")
replicate_files("CCLFA", file_date)     