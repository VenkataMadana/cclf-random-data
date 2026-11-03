import os
import random
import sys
import sys
from datetime import datetime
from faker import Faker
faker = Faker()

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import replicate_files
from utils import get_beneficiaries
from utils import bmsc, bdsc, beorcc, bebi

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
beneficiaries = list(get_beneficiaries().values())
beneficiaries_count = len(beneficiaries)

# Enumerate over the beneficiaries and emit to a temporary file.
file_name = "CCLF8.txt"
with open(f"{directory}/{file_name}", "w") as f:

    # Enumerate over the claims.
    for index, bene in enumerate(beneficiaries):    

        # Output a status message.
        if(index == 0 or index + 1 == beneficiaries_count or index % 1000 == 0):
            print(f"CCLF8 Processing for {file_date}: {int(100 * ((1 + index) / beneficiaries_count))}%", end="\r")     

        # Initialize.
        line = ""

        # 1-10
        line += bene["mbi"]                     # BENE_MBI_ID
        line += "".ljust(11)                    # BENE_HIC_NUM
        line += bene["fips_state"]              # BENE_FIPS_STATE_CD
        line += bene["fips_county"]             # BENE_FIPS_CNTY_CD
        line += bene["zipCode"].ljust(5)        # BENE_ZIP_CD
        line += bene["dob"]                     # BENE_DOB
        line += bene["gender"]                  # BENE_SEX_CD  
        line += bene["race"]                    # BENE_RACE_CD
        line += bene["age"].zfill(3)            # BENE_AGE
        line += random.choice(bmsc())           # BENE_MDCR_STUS_CD

        # 11-20
        line += random.choice(bdsc())           # BENE_DUAL_STUS_CD
        line += bene["dod"]                     # BENE_DEATH_DT
        line += bene["hospice_bgn"]             # BENE_RNG_BGN_DT
        line += bene["hospice_end"]             # BENE_RNG_END_DT
        line += bene["firstName"].ljust(30)     # BENE_1ST_NAME
        line += bene["middleName"].ljust(15)    # BENE_MIDL_NAME
        line += bene["lastName"].ljust(40)      # BENE_LAST_NAME
        line += random.choice(beorcc())         # BENE_ORGNL_ENTLMT_RSN_CD
        line += random.choice(bebi())           # BENE_ENTLMT_BUYIN_IND
        line += bene["part_a_bgn"]              # BENE_PART_A_ENRLMT_BGN_DT

        # # 21-30
        line += bene["part_b_bgn"]              # BENE_PART_B_ENRLMT_BGN_DT
        line += bene["address1"].ljust(45)      # BENE_LINE_1_ADR
        line += bene["address2"].ljust(45)      # BENE_LINE_2_ADR
        line += bene["address3"].ljust(40)      # BENE_LINE_3_ADR
        line += bene["address4"].ljust(40)      # BENE_LINE_4_ADR
        line += bene["address5"].ljust(40)      # BENE_LINE_5_ADR
        line += bene["address6"].ljust(40)      # BENE_LINE_6_ADR
        line += bene["city"].ljust(100)         # GEO_ZIP_PLC_NAME
        line += bene["state"]                   # GEO_USPS_STATE_CD
        line += bene["zipCode"]                 # GEO_ZIP5_CD

        # # 31-40
        line += bene["plus4"]                   # GEO_ZIP4_CD

        line += "\n"
        f.write(line)  
    
print(f"CCLF8 Processing for {file_date}: Complete")
replicate_files("CCLF8", file_date)             
