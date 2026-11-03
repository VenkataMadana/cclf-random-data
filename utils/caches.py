import calendar
import os
import pickle
import random
from datetime import date, timedelta
from faker import Faker
from utils import psc, brc, fips_state, fips_state_abbr, fips_counties_by_state, ctc
from utils import NULL_DATE, OPEN_END_DATE, MODELS

faker = Faker()

output_path = "./_output"
cache_path = f"{output_path}/cache"

beneficiaries = {}
providers = {}
claims = []

# Specifies the share of beneficiaries with each of these events.
deceased_rate = 0.05
hospice_rate = 0.05
mbi_change_rate = 0.05

# Specifies the share of claims in each claim family. Each family has its own
# files: A (CCLF1-4, CCLFA), B (CCLF5, CCLFB), DME (CCLF6), and D (CCLF7).
family_weights = { "A": 30, "B": 40, "DME": 10, "D": 20 }

# Claim Adjustment Type Codes (from the PDF).
ORIGINAL = "0"
CANCELLATION = "1"
ADJUSTMENT = "2"

# Specifies the share of first claims that are original and adjustment claims.
first_claim_weights = [90, 10]

# Specifies the share of original claims that are cancelled, and the share of
# those that are then replaced by an adjustment claim.
cancellation_rate = 0.05
readjustment_rate = 0.5

# Part D claim types and their adjustment types.
PART_D_DELETED = "03"
part_d_adjustments = { "01": ORIGINAL, "02": ADJUSTMENT, PART_D_DELETED: CANCELLATION }
part_d_type_weights = [85, 10, 5]

# ICD-10 replaced ICD-9 for services on or after this date.
icd10_start = date(2015, 10, 1)


def cache_all(number_of_beneficiaries, number_of_providers, number_of_claims, claims_year, claims_month):
    print("Creating Fake Data:")
    cache_beneficiaries(number_of_beneficiaries, claims_year, claims_month)
    cache_providers(number_of_providers)
    cache_claims(number_of_claims, claims_year, claims_month)
    cache_data("aco_ids", generate_aco_ids())
    cache_data("claims_year", claims_year)

def cache_beneficiaries(number_of_beneficiaries, claims_year, claims_month):
    print(f"\tBeneficiaries : {number_of_beneficiaries:,}")
    generate_beneficiaries(number_of_beneficiaries, claims_year, claims_month)
    cache_data("beneficiaries", beneficiaries)

def cache_providers(number_of_providers):
    print(f"\tProviders     : {number_of_providers:,}")
    generate_providers(number_of_providers)
    cache_data("providers", providers)    

def cache_claims(number_of_claims, claims_year, claims_month):
    print(f"\tClaims        : {number_of_claims:,}")
    generate_claims(number_of_claims, claims_year, claims_month)
    cache_data("claims", claims)


def generate_beneficiaries(quantity, claims_year, claims_month):
    period_start, period_end = get_month_range(claims_year, claims_month)
    for _ in range(quantity):

        dob = get_date_between(date(claims_year - 105, claims_month, 1), date(claims_year - 55, claims_month, 1))
        dod = get_date_between(period_start, period_end) if random.random() < deceased_rate else None
        part_a_bgn = get_entitlement_date(dob, period_start)
        part_b_bgn = get_date_between(part_a_bgn, period_start).replace(day=1)
        state_code = random.choice(fips_state())
        state = fips_state_abbr()[state_code]
        
        person = {
            "mbi": random_mbi(),
            "hic": "",

            "firstName": faker.first_name(),
            "middleName": faker.first_name(),
            "lastName": faker.last_name(),
            "gender": random.choice(["0", "1", "2"]),
            "dob": dob.strftime("%Y-%m-%d"),
            "dod": dod.strftime("%Y-%m-%d") if dod else NULL_DATE,
            "age": str(get_age(dob, dod or period_end)),
            "race": random.choice(brc()),
            "part_a_bgn": part_a_bgn.strftime("%Y-%m-%d"),
            "part_b_bgn": part_b_bgn.strftime("%Y-%m-%d"),
            "hospice_bgn": NULL_DATE,
            "hospice_end": NULL_DATE,
            "prev_mbi": "",
            
            "address1": faker.street_address(),
            "address2": faker.secondary_address(),
            "address3": faker.secondary_address(),
            "address4": faker.secondary_address(),
            "address5": faker.secondary_address(),
            "address6": faker.secondary_address(),
            "city": faker.city(),
            "state": state,
            "fips_state": state_code,
            "fips_county": random.choice(fips_counties_by_state()[state_code]),
            "zipCode": faker.zipcode_in_state(state),
            "plus4": faker.postalcode_plus4()[-4:]
        }

        # Hospice stays are still open unless the beneficiary has died.
        if random.random() < hospice_rate:
            earliest = max(part_a_bgn, period_start - timedelta(days=180))
            person["hospice_bgn"] = get_date_between(earliest, period_start).strftime("%Y-%m-%d")
            person["hospice_end"] = person["dod"] if dod else OPEN_END_DATE

        # Only beneficiaries with an MBI change are listed in CCLF9.
        if random.random() < mbi_change_rate:
            obsolete = get_date_between(part_a_bgn, period_start)
            person["prev_mbi"] = random_mbi()
            person["prev_mbi_efctv"] = get_date_between(part_a_bgn, obsolete).strftime("%Y-%m-%d")
            person["prev_mbi_obslt"] = obsolete.strftime("%Y-%m-%d")
        
        beneficiaries[person["mbi"]] = person


def generate_providers(quantity):
    for _ in range(quantity):
        state_code = random.choice(fips_state())
        state = fips_state_abbr()[state_code]
        provider = {
            "npi": "".join(random.choices("0123456789", k=10)),     # NPI
            "fnpi": "".join(random.choices("0123456789", k=10)),    # Facility NPI
            "oscar": "".join(random.choices("0123456789", k=6)),    # OSCAR/CCN
            "psc": random.choice(psc()),
            "ein": faker.ein(),
            
            "firstName": faker.first_name(),
            "middleName": faker.first_name(),
            "lastName": faker.last_name(),
            "gender": random.choice(["0", "1", "2"]),

            "address1": faker.street_address(),
            "address2": faker.secondary_address(),
            "city": faker.city(),
            "state": state,
            "fips_state": state_code,
            "zipCode": faker.zipcode_in_state(state),
            "plus4": faker.postalcode_plus4()[-4:]
        }
        
        providers[provider["npi"]] = provider


def generate_claims(quantity, claims_year, claims_month):
    period_start, period_end = get_month_range(claims_year, claims_month)
    file_date = period_end + timedelta(days=1)
    bene_list = list(beneficiaries.values())
    prov_list = list(providers.values())
    families = list(family_weights)
    weights = list(family_weights.values())

    while len(claims) < quantity:

        # Prepare the claim. Services cannot run past the month or a death.
        bene = random.choice(bene_list)
        prov = random.choice(prov_list)
        family = random.choices(families, weights)[0]
        last_date = period_end
        if bene["dod"] != NULL_DATE:
            last_date = date.fromisoformat(bene["dod"])
        claim_date = get_date_between(period_start, last_date)
        thru_date = get_date_between(claim_date, min(claim_date + timedelta(days=7), last_date))
        effective_date = get_date_between(thru_date, file_date)

        # Part D holds final action claims, so its type sets the adjustment type.
        if family == "D":
            claim_type = random.choices(ctc()[family], part_d_type_weights)[0]
            adjustment = part_d_adjustments[claim_type]
        else:
            claim_type = random.choice(ctc()[family])
            adjustment = random.choices([ORIGINAL, ADJUSTMENT], first_claim_weights)[0]

        # Generate the claim.
        claim = {
            "num": next_claim_num(claims_year, claims_month),
            "family": family,
            "ctc": claim_type,
            "adj": adjustment,
            "icd_ver": "0" if claim_date >= icd10_start else "9",
            "ccn": faker.numerify("A#######"),
            "ocn": faker.numerify("B#######"),
            "mac": faker.numerify("MC###"),
            "from_dt": claim_date.strftime("%Y-%m-%d"),
            "thru_dt": thru_date.strftime("%Y-%m-%d"),
            "efctv_dt": effective_date.strftime("%Y-%m-%d"),
            "pmt_amt": "0.00" if claim_type == PART_D_DELETED else paid_amount(),
            "mbi": bene["mbi"],
            "npi": prov["npi"],
            "lines": []
        }

        # Generate between 1 and 5 claim lines per claim.
        for icl in range(1, random.randint(1, 5) + 1):
            cld = get_date_between(claim_date, thru_date).strftime("%Y-%m-%d")
            line = {
                "ln": f"{icl}",
                "from_dt": cld,
                "thru_dt": cld,
                "pd_amt": paid_amount(),
            }

            claim["lines"].append(line)

        claims.append(claim)

        if family != "D" and adjustment == ORIGINAL and random.random() < cancellation_rate:
            generate_related_claims(claim, claims_year, claims_month, file_date)

    # Related claims can run past the quantity. Dropping the last claims keeps
    # every cancellation with its original.
    del claims[quantity:]


# Cancels an original claim, and sometimes replaces it with an adjustment claim.
# These keep the original's natural key: its beneficiary and provider, service
# dates, and control number.
def generate_related_claims(original, claims_year, claims_month, file_date):
    effective_date = get_date_between(date.fromisoformat(original["efctv_dt"]), file_date)
    related = {
        **original,
        "adj": CANCELLATION,
        "efctv_dt": effective_date.strftime("%Y-%m-%d"),
    }

    # Cancellation amounts are not signed, and match the original's amounts.
    claims.append({**related, "num": next_claim_num(claims_year, claims_month)})

    if random.random() < readjustment_rate:
        claims.append({
            **related,
            "num": next_claim_num(claims_year, claims_month),
            "adj": ADJUSTMENT,
            "pmt_amt": paid_amount(),
            "lines": [{**line, "pd_amt": paid_amount()} for line in original["lines"]],
        })


def next_claim_num(claims_year, claims_month):
    return f"{claims_year}{claims_month:02}{len(claims) + 1:07}"

def paid_amount():
    return f"{random.uniform(0, 9999):.2f}"


# Each model has one fake entity whose ID appears in all of its filenames.
def generate_aco_ids():
    return { model: faker.numerify("#" * length) for model, (length, _) in MODELS.items() }


# Cache data with key.
def cache_data(key, data):
    if not os.path.exists(cache_path):
        os.makedirs(cache_path, exist_ok=True)

    cache_file_path = f"{cache_path}/{key}.pkl"
    with open(f"{cache_file_path}", 'wb') as f:
        pickle.dump(data, f)

   
# Define the characters that can be used for each element of an MBI.
c = "123456789"
n = "0123456789"
a = "ACDEFGHJKMNPQRTUVWXY"
an = a + n

def random_mbi():
    return f"{random.choice(c)}{random.choice(a)}{random.choice(an)}{random.choice(n)}{random.choice(a)}{random.choice(an)}{random.choice(n)}{random.choice(a)}{random.choice(a)}{random.choice(n)}{random.choice(n)}"

def get_month_range(year, month):
    if not 1 <= month <= 12:
        raise ValueError("Invalid month. Month should be between 1 and 12.")
    _, last_day = calendar.monthrange(year, month)
    return date(year, month, 1), date(year, month, last_day)

def get_date_between(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def get_age(dob, on_date):
    return on_date.year - dob.year - ((on_date.month, on_date.day) < (dob.month, dob.day))

# Entitlement starts at 65, or earlier for those under 65 (e.g., disability).
def get_entitlement_date(dob, period_start):
    at_65 = date(dob.year + 65, dob.month, 1)
    if at_65 <= period_start:
        return at_65
    return get_date_between(date(dob.year + 55, dob.month, 1), period_start).replace(day=1)
