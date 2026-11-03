import random
import sys

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import dol, get_file_date, open_cache_file, print_progress, replicate_files
from utils import get_claims, get_bene, get_prov
from utils import icd, nprc, cbfc, csc, nhc, ffs, drg, cosc, cat, atc, csaic, cfc, cqc

file_date = get_file_date()

# Prepare data structures for lookups.
claims = get_claims("A")
claims_count = len(claims)

# Enumerate over the claims and emit to a temporary file.
with open_cache_file("CCLF1") as f:
    # Enumerate over the claims.
    for index, claim in enumerate(claims):

        # Output a status message.
        print_progress("CCLF1", file_date, index, claims_count)

        # Initialize.
        line = ""
        bene = get_bene(claim["mbi"])
        prov = get_prov(claim["npi"])

        # 1-10
        line += claim["num"].ljust(13)              # CUR_CLM_UNIQ_ID
        line += prov["oscar"]                       # PRVDR_OSCAR_NUM
        line += bene["mbi"]                         # BENE_MBI_ID
        line += bene["hic"].ljust(11)               # BENE_HIC_NUM
        line += claim["ctc"].ljust(2)               # CLM_TYPE_CD
        line += claim["from_dt"]                    # CLM_FROM_DT
        line += claim["thru_dt"]                    # CLM_THRU_DT
        line += random.choice(cbfc())               # CLM_BILL_FAC_TYPE_CD
        line += random.choice(csc())                # CLM_BILL_CLSFCTN_CD
        line += random.choice(icd(claim["icd_ver"]))["code"].rjust(7)     # PRNCPL_DGNS_CD

        # 11-20
        line += random.choice(icd(claim["icd_ver"]))["code"].rjust(7)     # ADMTG_DGNS_CD
        line += random.choice(nprc()).ljust(2)      # CLM_MDCR_NPMT_RSN_CD
        line += dol().rjust(17)                     # CLM_PMT_AMT
        line += random.choice(nhc())                # CLM_NCH_PRMRY_PYR_CD
        line += prov["fips_state"]                  # PRVDR_FAC_FIPS_ST_CD  
        line += random.choice(ffs()).ljust(2)       # BENE_PTNT_STUS_CD 
        line += random.choice(drg()).ljust(4)       # DGNS_DRG_CD
        line += random.choice(cosc())               # CLM_OP_SRVC_TYPE_CD
        line += prov["npi"]                         # FAC_PRVDR_NPI_NUM
        line += prov["npi"]                         # OPRTG_PRVDR_NPI_NUM

        # 21-30
        line += prov["npi"]                         # ATNDG_PRVDR_NPI_NUM
        line += prov["npi"]                         # OTHR_PRVDR_NPI_NUM
        line += random.choice(cat()).rjust(2)       # CLM_ADJSMT_TYPE_CD
        line += claim["thru_dt"]                    # CLM_EFCTV_DT
        line += claim["thru_dt"]                    # CLM_IDR_LD_DT
        line += bene["hic"].ljust(11)               # BENE_EQTBL_BIC_HICN_NUM
        line += random.choice(atc()).rjust(2)       # CLM_ADMSN_TYPE_CD   
        line += random.choice(csaic()).rjust(2)     # CLM_ADMSN_SRC_CD
        line += random.choice(cfc())                # CLM_BILL_FREQ_CD
        line += random.choice(cqc())                # CLM_QUERY_CD

        # 31-40
        line += claim["icd_ver"]                    # DGNS_PRCDR_ICD_IND
        line += dol().rjust(15)                     # CLM_MDCR_INSTNL_TOT_CHRG_AMT
        line += dol().rjust(15)                     # CLM_MDCR_IP_PPS_CPTL_IME_AMT
        line += dol().rjust(22)                     # CLM_OPRTNL_IME_AMT
        line += dol().rjust(15)                     # CLM_MDCR_IP_PPS_DSPRPRTNT_AMT
        line += dol().rjust(15)                     # CLM_HIPPS_UNCOMPD_CARE_AMT
        line += dol().rjust(22)                     # CLM_OPRTNL_DSPRPRTNT_AMT
        line += prov["oscar"].ljust(20)             # CLM_BLG_PRVDR_OSCAR_NUM
        line += prov["fnpi"]                        # CLM_BLG_PRVDR_NPI_NUM
        line += prov["npi"]                         # CLM_OPRTG_PRVDR_NPI_NUM

        # 41-45
        line += prov["npi"]                         # CLM_ATNDG_PRVDR_NPI_NUM
        line += prov["npi"]                         # CLM_OTHR_PRVDR_NPI_NUM
        line += claim["ccn"].rjust(40)              # CLM_CNTL_NUM
        line += claim["ocn"].rjust(40)              # CLM_ORG_CNTL_NUM
        line += claim["mac"]                        # CLM_CNTRCTR_NUM
        
        line += "\n"

        f.write(line)

replicate_files("CCLF1", file_date)
