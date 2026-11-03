# utils.py
import datetime
import os
import random
import pickle
import shutil
import sys
sys.path.append("./utils/reference")

from faker import Faker
from functools import lru_cache

from beneficiary_dual_status import get_codes as bdsc_get_codes
from beneficiary_entitlement_buy_in_indicator import get_codes as bebi_get_codes
from beneficiary_medicare_status import get_codes as bmcsc_get_codes
from beneficiary_original_entitlement_reason_code import get_codes as beorcc_get_codes
from beneficiary_race import get_codes as brc_get_codes
from carrier_payment_denial import get_codes as cpd_get_codes
from claim_adjustment_type import get_codes as catc_get_codes
from claim_admission_type  import get_codes as actc_get_codes
from claim_bill_facility_type import get_codes as cbfc_get_codes
from claim_dispensing import get_codes as cdsc_get_codes
from claim_disposition import get_codes as cdc_get_codes
from claim_frequency import get_codes as cfc_get_codes
from claim_outpatient_service_type import get_codes as cosc_get_codes
from ansi_group import get_codes as ansi_group_get_codes
from ansi_reason import get_codes as ansi_reason_get_codes
from claim_product_type import get_codes as ptc_get_codes
from claim_query import get_codes as cqc_get_codes
from claim_related_condition import get_codes as crc_get_codes
from claim_service_classification_type import get_codes as csc_get_codes
from claim_source_inpatient_admission import get_codes as csaic_get_codes
from claim_type import get_codes as ctc_get_codes
from daw_product_selection import get_codes as daw_get_codes
from drg import get_codes as drg_get_codes
from ffs_patient_discharge import get_codes as ffs_get_codes
from fips_county import get_codes as fips_county_get_codes
from fips_state import get_codes as fips_state_get_codes, get_abbreviations as fips_abbr_get_codes
from hcpcs import get_codes as hcpcs_get_codes
from hcpcs_mod import get_codes as hcpcs_mod_get_codes
from hipps import get_codes as hipps_get_codes
from hpsa_scarcity import get_codes as hpsa_get_codes
from icd import get_codes as icd_get_codes
from icd_procedure import get_codes as icd_procedure_get_codes
from nhc_primary_payer import get_codes as nhc_get_codes
from pharmacy_service_type import get_codes as pstc_get_codes
from place_of_service import get_codes as pos_get_codes
from present_on_admission import get_codes as poa_get_codes
from primary_payer import get_codes as ppc_get_codes
from processing_indicator import get_codes as pic_get_codes
from provider_service_identifier_qualifier import get_codes as psiqc_get_codes
from provider_specialty import get_codes as psc_get_codes
from reason_payment import get_codes as rpc_get_codes
from rendering_provider_type import get_codes as rptc_get_codes
from revenue_code import get_codes as revo_get_codes
from type_service import get_codes as tsc_get_codes

faker = Faker()

output_path = "./_output"
cache_path = f"{output_path}/cache"

# Dates used for missing values (section 3.6 of the PDF).
NULL_DATE = "1000-01-01"
OPEN_END_DATE = "9999-12-31"

# Describes each model's ID length and the run types (Y = monthly, R = run-out)
# used in its filenames.
MODELS = {
    "A": (4, "YR"),     # Shared Savings Program
    "F": (3, "YR"),     # VTAPM
    "D": (4, "YR"),     # ACO REACH
    "K": (4, "Y"),      # KCC (KCF option)
    "C": (4, "Y"),      # KCC (CKCC option)
    "P": (6, "Y"),      # PCF
}

# Describes the name and record length of each file type in the PDF.
FILE_TYPES = {
    "CCLF1": ("Part A Claims Header File.", 437),
    "CCLF2": ("Part A Claims Revenue Center Detail File.", 199),
    "CCLF3": ("Part A Procedure Code File.", 114),
    "CCLF4": ("Part A Diagnosis Code File.", 112),
    "CCLF5": ("Part B Physicians File.", 388),
    "CCLF6": ("Part B DME File.", 247),
    "CCLF7": ("Part D File.", 195),
    "CCLF8": ("Beneficiary Demographics File.", 549),
    "CCLF9": ("BENE XREF File.", 55),
    "CCLFA": ("Part A BE and Demo Codes File.", 324),
    "CCLFB": ("Part B BE and Demo Codes File.", 128),
}

# Seed from the script name too, so each script gets its own random sequence.
def seed_random(seed):
    scoped_seed = f"{seed}:{os.path.basename(sys.argv[0])}"
    random.seed(scoped_seed)
    Faker.seed(scoped_seed)

if "CCLF_SEED" in os.environ:
    seed_random(os.environ["CCLF_SEED"])

# Purge output directory
def purge_output_folder():
    if not os.path.exists(output_path):
        return
    
    # Iterate through all files and folders in the directory
    for filename in os.listdir(output_path):
        file_path = os.path.join(output_path, filename)
        
        # Check if it's a file or directory
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.remove(file_path)  # Remove the file or link
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)  # Remove the directory and its contents


@lru_cache(maxsize=None)
def get_beneficiaries():
    if os.path.exists(f"{cache_path}/beneficiaries.pkl"):
        with open(f"{cache_path}/beneficiaries.pkl", 'rb') as f:
            return pickle.load(f)
        
    return {}    


@lru_cache(maxsize=None)
def get_all_claims():
    if os.path.exists(f"{cache_path}/claims.pkl"):
        with open(f"{cache_path}/claims.pkl", 'rb') as f:
            return pickle.load(f)
        
    return []


# Returns the claims in a family: A, B, DME, or D.
def get_claims(family):
    return [claim for claim in get_all_claims() if claim["family"] == family]


@lru_cache(maxsize=None)
def get_aco_ids():
    with open(f"{cache_path}/aco_ids.pkl", 'rb') as f:
        return pickle.load(f)


@lru_cache(maxsize=None)
def get_providers():
    if os.path.exists(f"{cache_path}/providers.pkl"):
        with open(f"{cache_path}/providers.pkl", 'rb') as f:
            return pickle.load(f)
        
    return {}   


def get_bene(mbi):
    beneficiaries = get_beneficiaries()
    return beneficiaries[mbi]

def get_prov(npi):
    providers = get_providers()
    return providers[npi]

def fips_county():
    return fips_county_get_codes()

def fips_state():
    return fips_state_get_codes()

def fips_state_abbr():
    return fips_abbr_get_codes()

# The county list is in state order, with "000" marking the start of each state.
@lru_cache(maxsize=None)
def fips_counties_by_state():
    counties = {}
    states = iter(fips_state())
    for code in fips_county():
        if code == "000":
            state = next(states)
            counties[state] = []
        else:
            counties[state].append(code)
    return counties

def bdsc():
    return bdsc_get_codes()

def bebi():
    return bebi_get_codes()

def bmsc():
    return bmcsc_get_codes()

def beorcc():
    return beorcc_get_codes()

def brc():
    return brc_get_codes()

# Claim Admission Type Codes
def atc():
    return actc_get_codes()

# Claim Adjustment Type Codes
def cat():
    return catc_get_codes()

# Claim Bill Facility Type Codes
def cbfc():
    return cbfc_get_codes()

# Claim Outpatient Service Type Codes
def cosc():
    return cosc_get_codes()

# Claim Service Classification Type Codes
def ctc():
    return ctc_get_codes()

# Claim Medicare Non-Payment Reason Codes
def nprc():
    return rpc_get_codes()

# Claim Service Classification Type Codes
def csc():
    return csc_get_codes()

# NCH Primary Payer Code (if not Medicare)
def nhc():
    return nhc_get_codes()

# FFS Patient Discharge Code
def ffs():
    return ffs_get_codes()

# ICD diagnosis codes for a version indicator: 9 = ICD-9, 0 = ICD-10.
@lru_cache(maxsize=None)
def icd(ver):
    return [code for code in icd_get_codes() if code["ver"] == ver]

# ICD procedure codes for a version indicator: 9 = ICD-9, 0 = ICD-10.
@lru_cache(maxsize=None)
def pcs(ver):
    return [code for code in icd_procedure_get_codes() if code["ver"] == ver]

# CMS DRG / MSDRG Codes
def drg():
    return drg_get_codes()

def csaic():
    return csaic_get_codes()

def cfc():
    return cfc_get_codes()

def cqc():
    return cqc_get_codes()

def revcd():
    return revo_get_codes()

def hcpcs():
    return hcpcs_get_codes()

def hcpcsm():
    return hcpcs_mod_get_codes()

def hipps():
    return hipps_get_codes()

def cptc():
    return ptc_get_codes()

def poa():
    return poa_get_codes()

def rpt():
    return rptc_get_codes()

def psc():
    return psc_get_codes()

def tsc():
    return tsc_get_codes()

def pos():
    return pos_get_codes()

def ppc():
    return ppc_get_codes()

def cdc():
    return cdc_get_codes()

# Returns a current numberic following the pattern (-)#.##.
def dol():
    return f"{random.uniform(-99, 9999):.2f}"

# Returns a float following the pattern #.####.
def flt():
    return f"{random.uniform(0, 9999):.4f}"

def cpd():
    return cpd_get_codes()

def pic():
    return pic_get_codes()

def ndc():
    return faker.numerify("###########")

def psiqc():
    return psiqc_get_codes()

def cdsc():
    return cdsc_get_codes()

def daw():
    return daw_get_codes()

def rint():
    return str(random.randint(1, 365))

def pstc():
    return pstc_get_codes()

def ynb():
    return random.choice(["Y", "N", " "])

def twobyte():
    return f"{random.randint(0, 255):02X}"

def crc():
    return crc_get_codes()

def ansi_reason():
    return ansi_reason_get_codes()

def ansi_group():
    return ansi_group_get_codes()

def hpsa():
    return hpsa_get_codes()

# Returns the filenames for a ZC code across the models for a yymmdd date.
def get_file_names(code, date):
    ids = get_aco_ids()
    return [
        f"P.{model}{ids[model]}.ACO.ZC{code}{run}{date[:2]}.D{date}.T0102030"
        for model, (_, runs) in MODELS.items()
        for run in runs
    ]


def replicate_files(type, date):
    print(f"{type} for {date} processing...")

    # Create a date from the string.
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    date = date.strftime("%y%m%d")

    # Define the output path for the files.
    output_dir = f"{output_path}/{date}/{type}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Emit the generated data for the primary file.
    for file in get_file_names(type[-1], date):
        output_file = f"{output_dir}/{file}"
        print(f"\tCreating {type} {file}...")
        shutil.copy(f"{cache_path}/{type}.txt", output_file)


# Emit the Summary Statistics (CCLF0) after all of the other files are generated.
def write_summary_files(date):
    print(f"CCLF0 for {date} processing...")

    # Create a date from the string.
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    date = date.strftime("%y%m%d")

    # Define the output path for the files.
    output_dir = f"{output_path}/{date}/CCLF0"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Table 25
    header = f"{'File Number'.ljust(13)}|{'File Description'.ljust(20)}|{'Total Records Count'.ljust(20)}|{'Record Length'.ljust(13)}\n"

    # Table 26
    details = ""
    for type, (name, record_length) in FILE_TYPES.items():
        with open(f"{cache_path}/{type}.txt") as f:
            record_count = sum(1 for _ in f)
        details += f"{type.ljust(7)}|{name.ljust(43)}|{str(record_count).rjust(11)}|{str(record_length).rjust(5)} \n"

    for file in get_file_names("0", date):
        print(f"\tCreating CCLF0 {file}...")
        with open(f"{output_dir}/{file}", "w") as f:
            f.write(header)

            # Only these models receive Table 26.
            if file.startswith(("P.A", "P.F", "P.P")):
                f.write(details)
