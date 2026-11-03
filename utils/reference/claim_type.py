# Claim Type Codes, by claim family
# (from the PDF)
def get_codes():
    return {
        "A": [
            "10",      # HHA claim
            "20",      # Non swing bed SNF claim
            "30",      # Swing bed SNF claim
            "40",      # Outpatient claim
            "50",      # Hospice claim
            "60",      # Inpatient claim
            "61",      # Inpatient “Full-Encounter” claim
        ],
        "B": [
            "71",      # RIC O local carrier non-DMEPOS claim (CCLF5)
            "72",      # RIC O local carrier DMEPOS claim (CCLF5)
        ],
        "DME": [
            "81",      # RIC M DMERC non-DMEPOS claim (CCLF6)
            "82",      # RIC M DMERC DMEPOS claim (CCLF6)
        ],
        "D": [
            "01",      # Part D - Original without resubmitted PDE (CCLF7)
            "02",      # Part D - Adjusted PDE (CCLF7)
            "03",      # Part D - Deleted Claims (CCLF7)
        ],
    }
