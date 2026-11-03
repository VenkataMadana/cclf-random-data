import random
import sys

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import dol, get_file_date, open_cache_file, print_progress, replicate_files
from utils import get_claims, get_prov
from utils import tsc, pos, hcpcs, ppc, cpd, pic, cat, cdc, tsc

file_date = get_file_date()

# Prepare data structures for lookups.
claims = get_claims("DME")
claims_count = len(claims)

# Enumerate over the claims and emit to a temporary file.
with open_cache_file("CCLF6") as f:
    # Enumerate over the claims.
    for index, claim in enumerate(claims):

        # Output a status message.
        print_progress("CCLF6", file_date, index, claims_count)

        # Enumerate the claim lines.
        for claim_line in claim["lines"]:

            # Get the beneficiary and NPI provider.
            line = ""
            prov = get_prov(claim["npi"])

            # 1-10
            line += claim["num"].ljust(13)          # CUR_CLM_UNIQ_ID
            line += claim_line["ln"].zfill(10)      # CLM_LINE_NUM
            line += claim["mbi"]                    # BENE_MBI_ID
            line += "".ljust(11)                    # BENE_HIC_NUM
            line += claim["ctc"]                    # CLM_TYPE_CD
            line += claim["from_dt"]                # CLM_FROM_DT
            line += claim["thru_dt"]                # CLM_THRU_DT
            line += random.choice(tsc())            # CLM_FED_TYPE_SRVC_CD
            line += random.choice(pos())            # CLM_POS_CD
            line += claim_line["from_dt"]           # CLM_LINE_FROM_DT

            # 11-20
            line += claim_line["thru_dt"]           # CLM_LINE_THRU_DT   
            line += random.choice(hcpcs())          # CLM_LINE_HCPCS_CD
            line += str(dol()).rjust(15)            # CLM_LINE_CVRD_PD_AMT
            line += random.choice(ppc()).ljust(1)   # CLM_PRMRY_PYR_CD
            line += prov["npi"]                     # PAYTO_PRVDR_NPI_NUM
            line += prov["npi"]                     # ORDRG_PRVDR_NPI_NUM
            line += random.choice(cpd()).ljust(2)   # CLM_CARR_PMT_DNL_CD
            line += random.choice(pic()).ljust(2)   # CLM_PRCSG_IND_CD
            line += random.choice(cat()).ljust(2)   # CLM_ADJSMT_TYPE_CD
            line += claim["from_dt"]                # CLM_EFCTV_DT
            
            # 21-27
            line += claim["thru_dt"]                # CLM_IDR_LD_DT
            line += claim["ccn"].rjust(40)          # CLM_CNTL_NUM
            line += "".ljust(11)                    # BENE_EQTBL_BIC_HICN_NUM
            line += str(dol()).rjust(17)            # CLM_LINE_ALOWD_CHRG_AMT
            line += random.choice(cdc()).ljust(2)   # CLM_DISP_CD
            line += prov["npi"]                     # CLM_BLG_PRVDR_NPI_NUM
            line += prov["npi"]                     # CLM_RFRG_PRVDR_NPI_NUM

            line += "\n"

            f.write(line)

replicate_files("CCLF6", file_date)
