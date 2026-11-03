import calendar
import os
import pickle
import random
from datetime import date, timedelta
from itertools import accumulate
from faker import Faker
from utils import fips_state, fips_state_abbr, fips_counties_by_state, ctc, hcpcsm, hipps, nhc, nprc, ppc
from utils import NULL_DATE, OPEN_END_DATE, MODELS
from clinical import ACUTE_EPISODES, CONDITIONS, DME_SERVICES, DRUG_NDCS, PART_A_TYPES, ROUTINE_VISIT, SERVICES

faker = Faker()

output_path = "./_output"
cache_path = f"{output_path}/cache"

beneficiaries = {}
providers = {}
claims = []
market_states = []
provider_pools = {}

# Specifies the number of states in the market, and the share of patients in it.
market_size = 3
in_market_rate = 0.95

# Specifies the mix of ages, with most Medicare patients over 65.
age_bands = [(55, 64), (65, 74), (75, 84), (85, 100)]
age_band_weights = [12, 50, 28, 10]

# Specifies the mix of race codes.
race_codes = ["1", "2", "3", "4", "5", "6", "0"]
race_weights = [75, 10, 2, 3, 8, 1, 1]

# Specifies the share of patients with each of these events. Hospice is only for
# patients with a terminal condition, who are more likely to die this month.
deceased_rate = 0.02
hospice_rate = 0.15
hospice_death_rate = 0.3
mbi_change_rate = 0.05
under_65_dual_rate = 0.4
over_65_dual_rate = 0.12

# Specifies the share of providers in each role, and the specialties of primary
# care providers.
provider_roles = { "pcp": 40, "specialist": 30, "facility": 15, "pharmacy": 10, "dme": 5 }
pcp_specialties = ["01", "08", "11"]

# Specifies the share of claims in each claim family. Each family has its own
# files: A (CCLF1-4, CCLFA), B (CCLF5, CCLFB), DME (CCLF6), and D (CCLF7).
family_weights = { "A": 20, "B": 45, "DME": 5, "D": 30 }

# Specifies the share of claims with Medicare as the secondary payer, no Medicare
# payment, and a HCPCS modifier on a line.
other_payer_rate = 0.05
non_payment_rate = 0.03
modifier_rate = 0.2

INPATIENT_TYPES = ("60", "61")

# ICD-10 replaced ICD-9 for services on or after this date.
icd10_start = date(2015, 10, 1)

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

# The bill frequency, query, and disposition codes for each adjustment type.
adjustment_fields = {
    ORIGINAL: ("1", "3", "01"),
    CANCELLATION: ("8", "0", "03"),
    ADJUSTMENT: ("7", "5", "02"),
}


def cache_all(number_of_beneficiaries, number_of_providers, number_of_claims, claims_year, claims_month):
    print("Creating Fake Data:")
    choose_market()
    cache_providers(number_of_providers)
    cache_beneficiaries(number_of_beneficiaries, claims_year, claims_month)
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


# An ACO serves a region, so its providers and most of its patients are local.
def choose_market():
    market_states[:] = random.sample(fips_state(), market_size)


def generate_beneficiaries(quantity, claims_year, claims_month):
    period_start, period_end = get_month_range(claims_year, claims_month)
    for _ in range(quantity):

        gender = random.choices(["2", "1", "0"], [55, 44.5, 0.5])[0]
        low_age, high_age = random.choices(age_bands, age_band_weights)[0]
        birth_year = claims_year - random.randint(low_age, high_age)
        dob = get_date_between(date(birth_year - 1, claims_month, 1), date(birth_year, claims_month, 1))
        conditions = choose_conditions(gender, get_age(dob, period_end))
        terminal = [name for name in conditions if CONDITIONS[name].get("terminal")]
        hospice = bool(terminal) and random.random() < hospice_rate

        death_rate = hospice_death_rate if hospice else deceased_rate
        dod = get_date_between(period_start, period_end) if random.random() < death_rate else None
        age = get_age(dob, dod or period_end)
        part_a_bgn = get_entitlement_date(dob, period_start)
        part_b_bgn = get_date_between(part_a_bgn, period_start).replace(day=1)
        state_code = random.choice(market_states) if random.random() < in_market_rate else random.choice(fips_state())
        state = fips_state_abbr()[state_code]
        esrd = "esrd" in conditions
        dual = random.random() < (under_65_dual_rate if age < 65 else over_65_dual_rate)

        drugs = []
        for name in conditions:
            options = CONDITIONS[name]["drugs"]
            for drug in random.sample(options, random.randint(1, len(options))):
                if drug not in drugs:
                    drugs.append(drug)
        
        person = {
            "mbi": random_mbi(),
            "hic": "",

            "firstName": faker.first_name(),
            "middleName": faker.first_name(),
            "lastName": faker.last_name(),
            "gender": gender,
            "dob": dob.strftime("%Y-%m-%d"),
            "dod": dod.strftime("%Y-%m-%d") if dod else NULL_DATE,
            "age": str(age),
            "race": random.choices(race_codes, race_weights)[0],
            "part_a_bgn": part_a_bgn.strftime("%Y-%m-%d"),
            "part_b_bgn": part_b_bgn.strftime("%Y-%m-%d"),
            "hospice_bgn": NULL_DATE,
            "hospice_end": NULL_DATE,
            "prev_mbi": "",

            # Medicare status and entitlement follow from age and ESRD.
            "mdcr_status": ("1" if age >= 65 else "2") + ("1" if esrd else "0"),
            "orig_reason": get_entitlement_reason(age, esrd),
            "dual": random.choice(["01", "02", "03", "04", "06", "08"]) if dual else "NA",
            "buyin": "C" if dual else "3",

            # The patient's conditions, each with one diagnosis code position,
            # their regular drugs, and their care team.
            "conditions": conditions,
            "terminal": terminal,
            "drugs": drugs,
            "utilization": min(random.lognormvariate(0, 0.8), 3) * (1 + len(conditions)) ** 1.2,
            "pcp": find_provider("pcp", state_code),
            "hospital": find_provider("facility", state_code),
            "pharmacy": find_provider("pharmacy", state_code),
            "dme_supplier": find_provider("dme", state_code),
            "specialists": {
                CONDITIONS[name]["specialty"]: find_provider("specialist", state_code, CONDITIONS[name]["specialty"])
                for name in conditions
            },
            
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
        if hospice:
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


# Chooses a patient's conditions based on sex and age, with a fixed diagnosis
# code position for each so that the patient keeps the same code on every claim.
def choose_conditions(gender, age):
    age_factor = 0.6 if age < 65 else 1.0 if age < 75 else 1.3
    conditions = {}
    for name, condition in CONDITIONS.items():
        if condition.get("sex", gender) != gender or age < condition.get("min_age", 0):
            continue
        if random.random() < condition["prevalence"] * age_factor:
            conditions[name] = random.randrange(100)
    return conditions


def get_entitlement_reason(age, esrd):
    if age < 65:
        return "3" if esrd else "1"
    if esrd:
        return "2"
    return random.choices(["0", "1"], [85, 15])[0]


def generate_providers(quantity):
    specialties = sorted({ condition["specialty"] for condition in CONDITIONS.values() })
    for _ in range(quantity):
        state_code = random.choice(market_states)
        state = fips_state_abbr()[state_code]
        role = random.choices(list(provider_roles), provider_roles.values())[0]
        specialty = ""
        if role == "pcp":
            specialty = random.choice(pcp_specialties)
        elif role == "specialist":
            specialty = random.choice(specialties)
        provider = {
            "npi": "".join(random.choices("0123456789", k=10)),     # NPI
            "fnpi": "".join(random.choices("0123456789", k=10)),    # Facility NPI
            "oscar": "".join(random.choices("0123456789", k=6)),    # OSCAR/CCN
            "role": role,
            "psc": specialty,
            "ein": faker.ein(),
            
            "firstName": faker.first_name(),
            "middleName": faker.first_name(),
            "lastName": faker.last_name(),
            "gender": random.choice(["1", "2"]),

            "address1": faker.street_address(),
            "address2": faker.secondary_address(),
            "city": faker.city(),
            "state": state,
            "fips_state": state_code,
            "zipCode": faker.zipcode_in_state(state),
            "plus4": faker.postalcode_plus4()[-4:]
        }
        
        providers[provider["npi"]] = provider

        for key in (
            ("specialty_in_state", role, specialty, state_code),
            ("specialty", role, specialty),
            ("role_in_state", role, state_code),
            ("role", role),
            ("any",),
        ):
            provider_pools.setdefault(key, []).append(provider["npi"])


# Finds a provider near the patient, widening the search when a small provider
# population has nobody local. Doctors with the needed specialty come first.
def find_provider(role, state_code, specialty=None):
    keys = [("role_in_state", role, state_code), ("role", role), ("any",)]
    if specialty:
        keys[:0] = [("specialty_in_state", role, specialty, state_code), ("specialty", role, specialty)]
    for key in keys:
        if key in provider_pools:
            return random.choice(provider_pools[key])


def generate_claims(quantity, claims_year, claims_month):
    period_start, period_end = get_month_range(claims_year, claims_month)
    file_date = period_end + timedelta(days=1)
    bene_list = list(beneficiaries.values())
    cumulative_weights = list(accumulate(bene["utilization"] for bene in bene_list))

    # Tracks patients with a facility stay, and drugs filled this month.
    had_stay = set()
    filled = {}

    while len(claims) < quantity:

        # Sicker patients are chosen for more of the claims.
        bene = random.choices(bene_list, cum_weights=cumulative_weights)[0]
        family = choose_family(bene, filled)

        # Services cannot run past the month or a death.
        last_date = period_end
        if bene["dod"] != NULL_DATE:
            last_date = date.fromisoformat(bene["dod"])

        # Generate the claim.
        claim = {
            "num": next_claim_num(claims_year, claims_month),
            "family": family,
            "adj": random.choices([ORIGINAL, ADJUSTMENT], first_claim_weights)[0],
            "ccn": faker.numerify("A#######"),
            "ocn": faker.numerify("B#######"),
            "mac": faker.numerify("MC###"),
            "mbi": bene["mbi"],
            "dgns": [],
            "procs": [],
            "lines": [],
            **get_blank_fields(),
        }

        if family == "A":
            build_part_a_claim(claim, bene, period_start, last_date, had_stay)
        elif family == "B":
            build_part_b_claim(claim, bene, period_start, last_date)
        elif family == "DME":
            build_dme_claim(claim, bene, period_start, last_date)
        else:
            build_part_d_claim(claim, bene, period_start, last_date, filled)

        effective_date = get_date_between(date.fromisoformat(claim["thru_dt"]), file_date)
        claim["efctv_dt"] = effective_date.strftime("%Y-%m-%d")
        set_adjustment_fields(claim)
        price_claim(claim)
        claims.append(claim)

        if family != "D" and claim["adj"] == ORIGINAL and random.random() < cancellation_rate:
            generate_related_claims(claim, claims_year, claims_month, file_date)

    # Related claims can run past the quantity. Dropping the last claims keeps
    # every cancellation with its original.
    del claims[quantity:]


def get_blank_fields():
    return {
        "ctc": "", "icd_ver": "0", "from_dt": "", "thru_dt": "", "efctv_dt": "",
        "npi": "", "atnd_npi": "", "oprtg_npi": "", "ref_npi": "",
        "fac": "", "cls": "", "drg": "", "admit_dx": "", "adm_type": "", "adm_src": "",
        "op_type": "0", "status": "", "npmt": "", "msp": " ", "pos": "",
        "ndc": "", "rx_days": "", "rx_qty": "", "pharm": "",
        "pmt_amt": "0.00", "chg_amt": "0.00",
    }


# Patients without DME needs or unfilled drugs see a doctor instead.
def choose_family(bene, filled):
    family = random.choices(list(family_weights), family_weights.values())[0]
    if family == "DME" and not get_dme_conditions(bene):
        return "B"
    if family == "D" and not get_unfilled_drugs(bene, filled):
        return "B"
    return family


def get_dme_conditions(bene):
    return [name for name in bene["conditions"] if CONDITIONS[name]["dme"]]


def get_unfilled_drugs(bene, filled):
    return [drug for drug in bene["drugs"] if drug not in filled.get(bene["mbi"], set())]


# Returns the patient's diagnosis code for one of their conditions.
def get_patient_dx(bene, name, ver):
    codes = CONDITIONS[name]["dx"][ver]
    return codes[bene["conditions"][name] % len(codes)]


# Returns the reason for care and its diagnosis, with the patient's other
# conditions as secondary diagnoses.
def choose_reason(bene, ver, inpatient=False, chronic_rate=0.8, name=None):
    conditions = list(bene["conditions"])
    if name or (conditions and random.random() < (0.5 if inpatient else chronic_rate)):
        name = name or random.choice(conditions)
        reason = CONDITIONS[name]
        principal = get_patient_dx(bene, name, ver)
    else:
        reason = random.choice(ACUTE_EPISODES) if inpatient else ROUTINE_VISIT
        principal = random.choice(reason["dx"][ver])

    secondary = [get_patient_dx(bene, other, ver) for other in conditions if other != name]
    random.shuffle(secondary)
    diagnoses = [principal] + [code for code in secondary[:random.randint(0, 3)] if code != principal]
    return reason, diagnoses


def set_service_dates(claim, period_start, last_date, longest_stay):
    from_date = get_date_between(period_start, last_date)
    thru_date = min(from_date + timedelta(days=random.randint(0, longest_stay)), last_date)
    claim["from_dt"] = from_date.strftime("%Y-%m-%d")
    claim["thru_dt"] = thru_date.strftime("%Y-%m-%d")
    claim["icd_ver"] = "0" if from_date >= icd10_start else "9"
    return from_date, thru_date


def add_line(claim, from_date, thru_date, **fields):
    service_date = get_date_between(from_date, thru_date).strftime("%Y-%m-%d")
    claim["lines"].append({
        "ln": f"{len(claim['lines']) + 1}",
        "from_dt": service_date,
        "thru_dt": service_date,
        "units": "1.0000",
        "pd_amt": "0.00",
        "alw_amt": "0.00",
        "rev": "",
        "hcpcs": "",
        "hipps": "",
        "mdfr": random.choice(hcpcsm()) if random.random() < modifier_rate else "",
        "tos": "",
        "betos": "",
        **fields,
    })


def choose_part_a_type(bene, had_stay):
    # Outpatient care is the only option once a patient has had a facility stay.
    if bene["mbi"] in had_stay:
        return "40"
    if bene["hospice_bgn"] != NULL_DATE:
        return "50"
    types = list(PART_A_TYPES)
    return random.choices(types, [PART_A_TYPES[code][0] for code in types])[0]


def build_part_a_claim(claim, bene, period_start, last_date, had_stay):
    claim_type = choose_part_a_type(bene, had_stay)
    _, facility, classification, longest_stay, revenue_codes, _, _ = PART_A_TYPES[claim_type]
    inpatient = claim_type in INPATIENT_TYPES
    stay = claim_type != "40"

    # Hospice covers the rest of the month, for the patient's terminal condition.
    if claim_type == "50":
        from_date, thru_date = period_start, last_date
        claim["from_dt"] = from_date.strftime("%Y-%m-%d")
        claim["thru_dt"] = thru_date.strftime("%Y-%m-%d")
        claim["icd_ver"] = "0" if from_date >= icd10_start else "9"
    else:
        from_date, thru_date = set_service_dates(claim, period_start, last_date, longest_stay)

    name = random.choice(bene["terminal"]) if claim_type == "50" else None
    reason, diagnoses = choose_reason(bene, claim["icd_ver"], inpatient=stay, name=name)

    if stay:
        had_stay.add(bene["mbi"])

    # Hospital care is at the patient's hospital. Other facilities are local.
    claim["npi"] = bene["hospital"] if claim_type in ("40", "60", "61") else find_provider("facility", bene["fips_state"])
    claim["atnd_npi"] = bene["specialists"].get(reason["specialty"], bene["pcp"])
    claim["ctc"] = claim_type
    claim["fac"] = facility
    claim["cls"] = classification
    claim["dgns"] = diagnoses
    claim["msp"] = random.choice(nhc()) if random.random() < other_payer_rate else " "
    claim["npmt"] = random.choice(nprc()) if random.random() < non_payment_rate else ""
    claim["status"] = get_discharge_status(claim_type, bene, thru_date)

    if inpatient:
        procedures = reason["proc"][claim["icd_ver"]]
        emergency = not reason.get("surgical") and random.random() < 0.8
        claim["drg"] = random.choice(reason["drg"])
        claim["admit_dx"] = diagnoses[0]
        claim["adm_type"] = "1" if emergency else "3"
        claim["adm_src"] = "7" if emergency else "1"
        if procedures and (reason.get("surgical") or random.random() < 0.3):
            claim["procs"] = [random.choice(procedures)]
            claim["oprtg_npi"] = claim["atnd_npi"]
    elif claim_type in ("20", "30"):
        claim["adm_type"] = "3"
        claim["adm_src"] = "4"
    elif claim_type == "40":
        claim["op_type"] = random.choice(["1", "3"])

    # Skilled and home health care bill a HIPPS code on their first line.
    for index in range(random.randint(1, 5)):
        fields = { "rev": revenue_codes[index % len(revenue_codes)] }
        if claim_type in ("10", "20", "30") and index == 0:
            fields["hipps"] = random.choice(hipps())
        if claim_type == "40":
            fields["hcpcs"] = random.choice(reason["services"])
        add_line(claim, from_date, thru_date, **fields)


def get_discharge_status(claim_type, bene, thru_date):
    if thru_date.strftime("%Y-%m-%d") == bene["dod"]:
        return "40" if claim_type == "50" else "20"
    if claim_type == "50":
        return "30"
    if claim_type in INPATIENT_TYPES:
        return random.choices(["01", "03", "06"], [70, 15, 15])[0]
    return "01"


def build_part_b_claim(claim, bene, period_start, last_date):
    from_date, thru_date = set_service_dates(claim, period_start, last_date, 0)
    reason, diagnoses = choose_reason(bene, claim["icd_ver"])

    # Routine care, and most other visits, are with the patient's regular doctor.
    specialist = bene["specialists"].get(reason["specialty"])
    claim["npi"] = specialist if specialist and random.random() < 0.5 else bene["pcp"]
    claim["ref_npi"] = bene["pcp"]
    claim["ctc"] = random.choices(ctc()["B"], [95, 5])[0]
    claim["dgns"] = diagnoses
    claim["msp"] = random.choice(ppc()) if random.random() < other_payer_rate else ""
    claim["pos"] = random.choices(["11", "22"], [90, 10])[0]

    # Each visit bills an office visit, then the services for the reason.
    services = random.sample(reason["services"], random.randint(0, len(reason["services"])))
    for code in [random.choice(["99213", "99214"])] + services:
        tos, betos, _, _ = SERVICES[code]
        add_line(claim, from_date, thru_date, hcpcs=code, tos=tos, betos=betos)


def build_dme_claim(claim, bene, period_start, last_date):
    from_date, thru_date = set_service_dates(claim, period_start, last_date, 0)
    name = random.choice(get_dme_conditions(bene))
    _, diagnoses = choose_reason(bene, claim["icd_ver"], name=name)

    claim["npi"] = bene["dme_supplier"]
    claim["ref_npi"] = bene["pcp"]
    claim["ctc"] = random.choices(ctc()["DME"], [10, 90])[0]
    claim["dgns"] = diagnoses
    claim["msp"] = random.choice(ppc()) if random.random() < other_payer_rate else ""
    claim["pos"] = "12"

    for code in random.sample(CONDITIONS[name]["dme"], random.randint(1, len(CONDITIONS[name]["dme"]))):
        add_line(claim, from_date, thru_date, hcpcs=code, tos=DME_SERVICES[code][0])


def build_part_d_claim(claim, bene, period_start, last_date, filled):
    set_service_dates(claim, period_start, last_date, 0)
    drug = random.choice(get_unfilled_drugs(bene, filled))
    filled.setdefault(bene["mbi"], set()).add(drug)
    days = random.choices([30, 90], [75, 25])[0]

    # Part D holds final action claims, so its type sets the adjustment type.
    claim["ctc"] = random.choices(ctc()["D"], part_d_type_weights)[0]
    claim["adj"] = part_d_adjustments[claim["ctc"]]
    claim["npi"] = bene["pharmacy"]
    claim["ref_npi"] = bene["pcp"]
    claim["ndc"] = DRUG_NDCS[drug]
    claim["rx_days"] = str(days)
    claim["rx_qty"] = f"{days}.0000"
    claim["pharm"] = "6" if days == 90 else "1"


def set_adjustment_fields(claim):
    claim["freq"], claim["query"], claim["disp"] = adjustment_fields[claim["adj"]]


# Sets the amounts on a claim based on its type and services.
def price_claim(claim):
    if claim["family"] == "A":
        _, _, _, _, _, low, high = PART_A_TYPES[claim["ctc"]]
        total = 0 if claim["npmt"] else random.uniform(low, high)
        claim["pmt_amt"] = f"{total:.2f}"
        claim["chg_amt"] = f"{(total or random.uniform(low, high)) * random.uniform(1.5, 4):.2f}"

        # Revenue center lines add up to the claim's payment.
        share = round(total / len(claim["lines"]), 2)
        for line in claim["lines"]:
            line["pd_amt"] = f"{share:.2f}"
        claim["lines"][-1]["pd_amt"] = f"{total - share * (len(claim['lines']) - 1):.2f}"
    elif claim["family"] == "D":
        claim["pmt_amt"] = "0.00" if claim["ctc"] == PART_D_DELETED else f"{random.uniform(1, 80):.2f}"
    else:
        for line in claim["lines"]:
            low, high = get_service_range(claim["family"], line["hcpcs"])
            paid = random.uniform(low, high)
            line["pd_amt"] = f"{paid:.2f}"
            line["alw_amt"] = f"{paid / 0.8:.2f}"


def get_service_range(family, code):
    return SERVICES[code][2:] if family == "B" else DME_SERVICES[code][1:]


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
    set_adjustment_fields(related)

    # Cancellation amounts are not signed, and match the original's amounts.
    claims.append({**related, "num": next_claim_num(claims_year, claims_month)})

    if random.random() < readjustment_rate:
        adjustment = {
            **related,
            "num": next_claim_num(claims_year, claims_month),
            "adj": ADJUSTMENT,
            "lines": [dict(line) for line in original["lines"]],
        }
        set_adjustment_fields(adjustment)
        price_claim(adjustment)
        claims.append(adjustment)


def next_claim_num(claims_year, claims_month):
    return f"{claims_year}{claims_month:02}{len(claims) + 1:07}"


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
