import sys

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import get_file_date, open_cache_file, print_progress, replicate_files
from utils import get_claims, get_prov
from utils import dgns_slot

file_date = get_file_date()

# Prepare data structures for lookups.
claims = get_claims("B")
claims_count = len(claims)

# Enumerate over the claims and emit to a temporary file.
with open_cache_file("CCLF5") as f:
    # Enumerate over the claims.
    for index, claim in enumerate(claims):

        # Output a status message.
        print_progress("CCLF5", file_date, index, claims_count)

        # Enumerate the claim lines.
        for claim_line in claim["lines"]:

            # Initialize.
            line = ""
            prov = get_prov(claim["npi"])

            # 1-10
            line += claim["num"].ljust(13)                  # CUR_CLM_UNIQ_ID
            line += claim_line["ln"].zfill(10)              # CLM_LINE_NUM
            line += claim["mbi"]                            # BENE_MBI_ID
            line += "".ljust(11)                            # BENE_HIC_NUM
            line += claim["ctc"]                            # CLM_TYPE_CD
            line += claim["from_dt"]                        # CLM_FROM_DT
            line += claim["thru_dt"]                        # CLM_THRU_DT
            line += "1".ljust(3)                            # RNDRG_PRVDR_TYPE_CD
            line += prov["fips_state"]                      # RNDRG_PRVDR_FIPS_ST_CD
            line += prov["psc"]                             # CLM_PRVDR_SPCLTY_CD

            # 11-20
            line += claim_line["tos"]                       # CLM_FED_TYPE_SRVC_CD
            line += claim["pos"]                            # CLM_POS_CD
            line += claim_line["from_dt"]                   # CLM_LINE_FROM_DT
            line += claim_line["thru_dt"]                   # CLM_LINE_THRU_DT    
            line += claim_line["hcpcs"].ljust(5)            # CLM_LINE_HCPCS_CD
            line += claim_line["pd_amt"].rjust(15)          # CLM_LINE_CVRD_PD_AMT
            line += claim["msp"].ljust(1)                   # CLM_LINE_PRMRY_PYR_CD
            line += claim["dgns"][0].rjust(7)               # CLM_LINE_DGNS_CD
            line += prov["ein"].rjust(10)                   # CLM_RNDRG_PRVDR_TAX_NUM
            line += prov["npi"]                             # RNDRG_PRVDR_NPI_NUM

            # 21-30
            line += "1".ljust(2)                            # CLM_CARR_PMT_DNL_CD
            line += "A".ljust(2)                            # CLM_PRCSG_IND_CD
            line += claim["adj"].ljust(2)                   # CLM_ADJSMT_TYPE_CD
            line += claim["efctv_dt"]                       # CLM_EFCTV_DT
            line += claim["efctv_dt"]                       # CLM_IDR_LD_DT
            line += claim["ccn"].rjust(40)                  # CLM_CNTL_NUM
            line += "".ljust(11)                            # BENE_EQTBL_BIC_HICN_NUM
            line += claim_line["alw_amt"].rjust(17)         # CLM_LINE_ALOWD_CHRG_AMT
            line += claim_line["units"].rjust(24)           # CLM_LINE_SRVC_UNIT_QTY
            line += claim_line["mdfr"].ljust(2)             # HCPCS_1_MDFR_CD

            # 31-40
            line += "".ljust(2)                             # HCPCS_2_MDFR_CD
            line += "".ljust(2)                             # HCPCS_3_MDFR_CD
            line += "".ljust(2)                             # HCPCS_4_MDFR_CD
            line += "".ljust(2)                             # HCPCS_5_MDFR_CD
            line += claim["disp"]                           # CLM_DISP_CD
            line += dgns_slot(claim, 0)                                     # CLM_DGNS_1_CD
            line += dgns_slot(claim, 1)                                     # CLM_DGNS_2_CD
            line += dgns_slot(claim, 2)                                     # CLM_DGNS_3_CD
            line += dgns_slot(claim, 3)                                     # CLM_DGNS_4_CD
            line += dgns_slot(claim, 4)                                     # CLM_DGNS_5_CD

            # #41-50
            line += dgns_slot(claim, 5)                                     # CLM_DGNS_6_CD
            line += dgns_slot(claim, 6)                                     # CLM_DGNS_7_CD
            line += dgns_slot(claim, 7)                                     # CLM_DGNS_8_CD
            line += claim["icd_ver"]                        # DGNS_PRCDR_ICD_IND
            line += dgns_slot(claim, 8)                                     # CLM_DGNS_9_CD
            line += dgns_slot(claim, 9)                                     # CLM_DGNS_10_CD
            line += dgns_slot(claim, 10)                                    # CLM_DGNS_11_CD
            line += dgns_slot(claim, 11)                                    # CLM_DGNS_12_CD
            line += claim_line["betos"].ljust(3)            # HCPCS_BETOS_CD
            line += prov["npi"].ljust(10)                   # CLM_RNDRG_PRVDR_NPI_NUM

            # 51-60
            line += claim["ref_npi"]                        # CLM_RFRG_PRVDR_NPI_NUM
            line += claim["mac"]                            # CLM_CNTRCTR_NUM
            line += "\n"

            f.write(line)

replicate_files("CCLF5", file_date)
