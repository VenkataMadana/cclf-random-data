import random
import sys

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import get_file_date, open_cache_file, print_progress, replicate_files
from utils import get_claims, get_prov

file_date = get_file_date()

# Prepare data structures for lookups.
claims = get_claims("A")
claims_count = len(claims)

# Enumerate over the claims and emit to a temporary file.
with open_cache_file("CCLF4") as f:
    # Enumerate over the claims.
    for index, claim in enumerate(claims):

        # Output a status message.
        print_progress("CCLF4", file_date, index, claims_count)

        # Get the NPI provider.
        prov = get_prov(claim["npi"])

        # Each of the claim's diagnoses has a record, starting with the principal.
        for sequence, diagnosis in enumerate(claim["dgns"], start=1):
            line = ""

            # Only inpatient claims report diagnoses as present on admission.
            present_on_admission = ""
            if claim["ctc"] in ("60", "61"):
                present_on_admission = random.choices(["Y", "N"], [90, 10])[0]

            # 1-10
            line += claim["num"].ljust(13)          # CUR_CLM_UNIQ_ID
            line += claim["mbi"]                    # BENE_MBI_ID
            line += "".ljust(11)                    # BENE_HIC_NUM
            line += claim["ctc"]                    # CLM_TYPE_CD
            line += "D"                             # CLM_PROD_TYPE_CD
            line += f"{sequence:02}"                # CLM_VAL_SQNC_NUM
            line += diagnosis.rjust(7)              # CLM_DGNS_CD
            line += "".ljust(11)                    # BENE_EQTBL_BIC_HICN_NUM
            line += prov["oscar"].rjust(6)          # PRVDR_OSCAR_NUM
            line += claim["from_dt"]                # CLM_FROM_DT

            # 11-13
            line += claim["thru_dt"]                # CLM_THRU_DT   
            line += present_on_admission.rjust(7)   # CLM_POA_IND
            line += claim["icd_ver"]                # DGNS_PRCDR_ICD_IND
            line += prov["oscar"].ljust(20)         # CLM_BLG_PRVDR_OSCAR_NUM
            line += "\n"

            f.write(line)

replicate_files("CCLF4", file_date)
