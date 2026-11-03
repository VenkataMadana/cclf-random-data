import sys

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import get_file_date, open_cache_file, print_progress, replicate_files
from utils import get_claims, get_bene, get_prov
from utils import pps_amt

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
        line += claim["fac"]                        # CLM_BILL_FAC_TYPE_CD
        line += claim["cls"]                        # CLM_BILL_CLSFCTN_CD
        line += claim["dgns"][0].rjust(7)                                 # PRNCPL_DGNS_CD

        # 11-20
        line += claim["admit_dx"].rjust(7)                                # ADMTG_DGNS_CD
        line += claim["npmt"].ljust(2)              # CLM_MDCR_NPMT_RSN_CD
        line += claim["pmt_amt"].rjust(17)          # CLM_PMT_AMT
        line += claim["msp"]                        # CLM_NCH_PRMRY_PYR_CD
        line += prov["fips_state"]                  # PRVDR_FAC_FIPS_ST_CD  
        line += claim["status"].ljust(2)            # BENE_PTNT_STUS_CD
        line += claim["drg"].ljust(4)               # DGNS_DRG_CD
        line += claim["op_type"]                    # CLM_OP_SRVC_TYPE_CD
        line += prov["npi"]                         # FAC_PRVDR_NPI_NUM
        line += claim["oprtg_npi"].ljust(10)        # OPRTG_PRVDR_NPI_NUM

        # 21-30
        line += claim["atnd_npi"]                   # ATNDG_PRVDR_NPI_NUM
        line += "".ljust(10)                        # OTHR_PRVDR_NPI_NUM
        line += claim["adj"].ljust(2)               # CLM_ADJSMT_TYPE_CD
        line += claim["efctv_dt"]                   # CLM_EFCTV_DT
        line += claim["efctv_dt"]                   # CLM_IDR_LD_DT
        line += bene["hic"].ljust(11)               # BENE_EQTBL_BIC_HICN_NUM
        line += claim["adm_type"].rjust(2)          # CLM_ADMSN_TYPE_CD
        line += claim["adm_src"].rjust(2)           # CLM_ADMSN_SRC_CD
        line += claim["freq"]                       # CLM_BILL_FREQ_CD
        line += claim["query"]                      # CLM_QUERY_CD

        # 31-40
        line += claim["icd_ver"]                    # DGNS_PRCDR_ICD_IND
        line += claim["chg_amt"].rjust(15)          # CLM_MDCR_INSTNL_TOT_CHRG_AMT
        line += pps_amt(claim).rjust(15)            # CLM_MDCR_IP_PPS_CPTL_IME_AMT
        line += pps_amt(claim).rjust(22)            # CLM_OPRTNL_IME_AMT
        line += pps_amt(claim).rjust(15)            # CLM_MDCR_IP_PPS_DSPRPRTNT_AMT
        line += pps_amt(claim).rjust(15)            # CLM_HIPPS_UNCOMPD_CARE_AMT
        line += pps_amt(claim).rjust(22)            # CLM_OPRTNL_DSPRPRTNT_AMT
        line += prov["oscar"].ljust(20)             # CLM_BLG_PRVDR_OSCAR_NUM
        line += prov["fnpi"]                        # CLM_BLG_PRVDR_NPI_NUM
        line += claim["oprtg_npi"].ljust(10)        # CLM_OPRTG_PRVDR_NPI_NUM

        # 41-45
        line += claim["atnd_npi"]                   # CLM_ATNDG_PRVDR_NPI_NUM
        line += "".ljust(10)                        # CLM_OTHR_PRVDR_NPI_NUM
        line += claim["ccn"].rjust(40)              # CLM_CNTL_NUM
        line += claim["ocn"].rjust(40)              # CLM_ORG_CNTL_NUM
        line += claim["mac"]                        # CLM_CNTRCTR_NUM
        
        line += "\n"

        f.write(line)

replicate_files("CCLF1", file_date)
