import sys

# Add the path of the folder where the module is located
sys.path.append("./utils/")
from utils import get_file_date, open_cache_file, print_progress, replicate_files
from utils import get_beneficiaries

file_date = get_file_date()

# Prepare data structures for lookups. Only beneficiaries with an MBI change
# appear in this file.
beneficiaries = [bene for bene in get_beneficiaries().values() if bene["prev_mbi"]]
beneficiaries_count = len(beneficiaries)

# Enumerate over the beneficiaries and emit to a temporary file.
with open_cache_file("CCLF9") as f:

    # Enumerate over the claims.
    for index, bene in enumerate(beneficiaries):    

        # Output a status message.
        print_progress("CCLF9", file_date, index, beneficiaries_count)

        # Initialize.
        line = ""

        # 1-6
        line += "M"                     # HICN_MBI_XREF_IND
        line += bene["mbi"]             # CRNT_NUM
        line += bene["prev_mbi"]        # PRVS_NUM
        line += bene["prev_mbi_efctv"]  # PRVS_ID_EFCTV_DT
        line += bene["prev_mbi_obslt"]  # PRVS_ID_OBSLT_DT
        line += "".ljust(12)            # BENE_RRB_NUM

        line += "\n"

        f.write(line)

replicate_files("CCLF9", file_date)
