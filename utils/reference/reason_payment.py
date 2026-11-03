# Claim Medicare Non-Payment Reason Code
# https://resdac.org/cms-data/variables/claim-medicare-non-payment-reason-code
def get_codes():
    return [
        "A",      # Covered worker's compensation (Obsolete)
        "B",      # Benefit exhausted
        "C",      # Custodial care - non-covered care(includes all 'beneficiary at fault' waiver cases) (Obsolete)
        "E",      # HMO out-of-plan services not emergency or urgently needed (Obsolete)
        "E",      # MSP cost avoided - IRS/SSA/HCFA Data Match (eff. 7/2000)
        "F",      # MSP cost avoids HMO Rate Cell (eff. 7/2000)
        "G",      # MSP cost avoided Litigation Settlement (eff. 7/2000)
        "H",      # MSP cost avoided EmployerVoluntary Reporting (eff. 7/2000)
        "J",      # MSP cost avoids Insurer Voluntary Reporting (eff. 7/2000)
        "K",      # MSP cost avoids Initial Enrollment Questionnaire (eff. 7/2000)
        "N",      # All other reasons for non-payment
        "P",      # Payment requested
        "Q",      # MSP cost avoided Voluntary Agreement (eff. 7/2000)
        "R",      # Benefits refused, or evidence not submitted
        "T",      # MSP cost avoided - IEQ contractor (eff. 9/1976) (obsolete 6/30/2000)
        "U",      # MSP cost avoided - HMO rate cell adjustment (eff. 9/1976) (Obsolete 6/30/2000)
        "V",      # MSP cost avoided - litigation settlement (eff. 9/1976) (Obsolete 6/30/2000)
        "W",      # Worker's compensation (Obsolete)
        "X",      # MSP cost avoided - generic
        "Y",      # MSP cost avoided - IRS/SSA data match project (obsolete 6/30/2000)
        "Z",      # Zero reimbursement RAPs zero reimbursement made due to medical review intervention or where provider specific zero payment has been determined. (eff. with HHPPS - 10/2000)
        "00",     # MSP cost avoided - COB Contractor
        "12",     # MSP cost avoided - BCBS Voluntary Agreements
        "13",     # MSP cost avoided - Office of Personnel Management
        "14",     # MSP cost avoided - Workman's Compensation (WC) Datamatch
        "15",     # MSP cost avoided - Workman's Compensation Insurer Voluntary Data Sharing Agreements (WC VDSA) (eff. 4/2006)
        "16",     # MSP cost avoided - Liability Insurer VDSA (eff. 4/2006)
        "17",     # MSP cost avoided - No-Fault Insurer VDSA (eff. 4/2006)
        "18",     # MSP cost avoided - Pharmacy Benefit Manager Data Sharing Agreement (eff. 4/2006)
        "19",     # REFERENCE NOTE4: Coordination of Benefits Contractor 11119 (reference CMS Change Request 7906 for identification of the contractor.)
        "21",     # MSP cost avoided - MIR Group Health Plan (eff. 1/2009)
        "22",     # MSP cost avoided - MIR non-Group Health Plan (eff. 1/2009)
        "25",     # MSP cost avoided - Recovery Audit Contractor - California (eff. 10/2005)
        "26",     # MSP cost avoided - Recovery Audit Contractor - Florida (eff. 10/2005)
        "42",     # REFERENCE NOTE4: Coordination of Benefits Contractor 11142 (reference CMS Change Request 7906 for identification of the contractor.)
        "43",     # REFERENCE NOTE4: Coordination of Benefits Contractor 11143 (reference CMS Change Request 7906 for identification of the contractor.)
    ]
