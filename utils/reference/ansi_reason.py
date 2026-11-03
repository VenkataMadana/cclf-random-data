# Sample Claim Adjustment Reason Codes (CARC)
def get_codes():
    return [
        "1",    # Deductible amount
        "2",    # Coinsurance amount
        "3",    # Co-payment amount
        "45",   # Charge exceeds fee schedule/maximum allowable
        "50",   # Non-covered services that are not deemed a medical necessity
        "96",   # Non-covered charge(s)
        "97",   # Payment is included in the allowance for another service/procedure
        "253",  # Sequestration - reduction in federal payment
    ]
