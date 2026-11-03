# Indicates the diagnostic related group to which a hospital claim belongs for prospective payment purposes.
# Excludes the alcohol and substance abuse DRGs in Appendix A of the PDF because
# CMS removes those claims from the CCLFs.
def get_codes():
    return [
        "189",  # MS-DRG Pulmonary edema and respiratory failure
        "190",  # MS-DRG Chronic obstructive pulmonary disease w MCC
        "194",  # MS-DRG Simple pneumonia and pleurisy w CC
        "291",  # MS-DRG Heart failure and shock w MCC
        "470",  # MS-DRG Major joint replacement of lower extremity w/o MCC
        "871",  # MS-DRG Septicemia or severe sepsis w/o MV >96 hours w MCC
   ]
