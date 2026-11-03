import random
import sys

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import dol, get_file_date, open_cache_file, print_progress, replicate_files
from utils import get_claims, get_prov
from utils import revcd, hcpcs, flt, hcpcsm, hipps

file_date = get_file_date()

# Prepare data structures for lookups.
claims = get_claims("A")
claims_count = len(claims)

# Enumerate over the claims and emit to a temporary file.
with open_cache_file("CCLF2") as f:
    # Enumerate over the claims.
    for index, claim in enumerate(claims):

        # Output a status message.
        print_progress("CCLF2", file_date, index, claims_count)

        # Enumerate the claim lines.
        for claim_line in claim["lines"]:

            # Get the beneficiary and NPI provider.
            line = ""
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
            line += prov["oscar"].ljust(20)             # CLM_FAC_PRVDR_OSCAR_NUM

            line += "\n"

            f.write(line)

replicate_files("CCLF2", file_date)
