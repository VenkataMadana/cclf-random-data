# Sample Claim Related Condition Codes
def get_codes():
    return [
        "02",   # Condition is employment related
        "03",   # Patient covered by insurance not reflected here
        "04",   # Information only bill
        "05",   # Lien has been filed
        "06",   # ESRD patient in first 30 months of entitlement covered by employer group health insurance
        "08",   # Beneficiary would not provide information concerning other insurance coverage
        "09",   # Neither patient nor spouse is employed
        "10",   # Patient and/or spouse is employed but no employer group health plan exists
    ]
