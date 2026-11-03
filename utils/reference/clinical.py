# Sample clinical data that keeps the codes on a patient's claims related to each
# other. Codes are samples, not a complete list, and exclude the alcohol and
# substance abuse codes in Appendix A of the PDF because CMS removes those claims
# from the CCLFs. Diagnosis and procedure codes have no decimal, and are listed
# by ICD version indicator: 0 = ICD-10, 9 = ICD-9.

# Placeholder drugs. The NDCs use a fake labeler code and are not real products.
DRUG_NAMES = [
    "albuterol", "amlodipine", "anastrozole", "apixaban", "atorvastatin",
    "bicalutamide", "calcitriol", "carvedilol", "clopidogrel", "donepezil",
    "furosemide", "glipizide", "lisinopril", "meloxicam", "memantine",
    "metformin", "sertraline", "sevelamer", "tiotropium", "warfarin",
]
DRUG_NDCS = { name: f"99999{index + 1:06}" for index, name in enumerate(DRUG_NAMES) }

# Chronic conditions. prevalence is the share of patients aged 65-74 who have
# the condition. terminal conditions can lead to hospice enrollment. A surgical
# condition's inpatient stays always include its procedure.
CONDITIONS = {
    "hypertension": {
        "prevalence": 0.55, "specialty": "11",
        "dx": { "0": ["I10"], "9": ["4019"] },
        "drg": ["304", "305"], "proc": { "0": [], "9": [] },
        "services": ["93000", "80053"], "dme": [], "drugs": ["lisinopril", "amlodipine"],
    },
    "diabetes": {
        "prevalence": 0.28, "specialty": "46",
        "dx": { "0": ["E119", "E1165", "E1122", "E1140"], "9": ["25000", "25060", "25040"] },
        "drg": ["637", "638", "639"], "proc": { "0": [], "9": [] },
        "services": ["83036", "82947", "80061"], "dme": ["A4253", "E0607"], "drugs": ["metformin", "glipizide"],
    },
    "coronary_artery_disease": {
        "prevalence": 0.25, "specialty": "06", "surgical": True,
        "dx": { "0": ["I2510", "I252"], "9": ["41401", "412"] },
        "drg": ["321", "322"], "proc": { "0": ["02703DZ"], "9": ["3606"] },
        "services": ["93000", "93306", "80061"], "dme": [], "drugs": ["atorvastatin", "clopidogrel"],
    },
    "heart_failure": {
        "prevalence": 0.13, "specialty": "06", "terminal": True,
        "dx": { "0": ["I5022", "I5032", "I509"], "9": ["42822", "42832", "4280"] },
        "drg": ["291", "292", "293"], "proc": { "0": ["4A023N7"], "9": ["3722"] },
        "services": ["93306", "93000", "71046"], "dme": ["E1390"], "drugs": ["furosemide", "carvedilol", "lisinopril"],
    },
    "atrial_fibrillation": {
        "prevalence": 0.09, "specialty": "06",
        "dx": { "0": ["I4891", "I4820"], "9": ["42731"] },
        "drg": ["308", "309", "310"], "proc": { "0": ["5A2204Z"], "9": ["9961"] },
        "services": ["93000", "85610"], "dme": [], "drugs": ["apixaban", "warfarin"],
    },
    "copd": {
        "prevalence": 0.14, "specialty": "29", "terminal": True,
        "dx": { "0": ["J449", "J441"], "9": ["496", "49121"] },
        "drg": ["190", "191", "192"], "proc": { "0": ["5A1945Z"], "9": ["9671"] },
        "services": ["94010", "71046"], "dme": ["E1390", "E0570"], "drugs": ["tiotropium", "albuterol"],
    },
    "chronic_kidney_disease": {
        "prevalence": 0.20, "specialty": "39",
        "dx": { "0": ["N1830", "N184"], "9": ["5853", "5854"] },
        "drg": ["682", "683", "684"], "proc": { "0": [], "9": [] },
        "services": ["80053"], "dme": [], "drugs": ["calcitriol"],
    },
    "esrd": {
        "prevalence": 0.01, "specialty": "39", "terminal": True,
        "dx": { "0": ["N186"], "9": ["5856"] },
        "drg": ["682", "683"], "proc": { "0": ["5A1D70Z"], "9": ["3995"] },
        "services": ["90935", "80053"], "dme": [], "drugs": ["sevelamer", "calcitriol"],
    },
    "dementia": {
        "prevalence": 0.08, "specialty": "13", "terminal": True, "min_age": 65,
        "dx": { "0": ["G309", "F0390"], "9": ["3310", "2900"] },
        "drg": ["056", "057"], "proc": { "0": [], "9": [] },
        "services": ["96116", "70551"], "dme": [], "drugs": ["donepezil", "memantine"],
    },
    "depression": {
        "prevalence": 0.17, "specialty": "26",
        "dx": { "0": ["F329", "F331"], "9": ["311", "29630"] },
        "drg": ["885"], "proc": { "0": [], "9": [] },
        "services": ["90834", "96127"], "dme": [], "drugs": ["sertraline"],
    },
    "osteoarthritis": {
        "prevalence": 0.30, "specialty": "20", "surgical": True,
        "dx": { "0": ["M170", "M1711", "M1611"], "9": ["71536", "71535"] },
        "drg": ["469", "470"], "proc": { "0": ["0SRC0J9"], "9": ["8154"] },
        "services": ["20610", "73562"], "dme": ["E0143", "L1833"], "drugs": ["meloxicam"],
    },
    "breast_cancer": {
        "prevalence": 0.05, "specialty": "90", "surgical": True, "terminal": True, "sex": "2",
        "dx": { "0": ["C50911", "C50912"], "9": ["1749"] },
        "drg": ["582", "583"], "proc": { "0": ["0HTU0ZZ"], "9": ["8541"] },
        "services": ["77067", "96413"], "dme": [], "drugs": ["anastrozole"],
    },
    "prostate_cancer": {
        "prevalence": 0.08, "specialty": "34", "surgical": True, "terminal": True, "sex": "1",
        "dx": { "0": ["C61"], "9": ["185"] },
        "drg": ["707", "708"], "proc": { "0": ["0VT04ZZ"], "9": ["605"] },
        "services": ["84153", "77427"], "dme": [], "drugs": ["bicalutamide"],
    },
}

# Conditions that can bring any patient into the hospital.
ACUTE_EPISODES = [
    {
        "specialty": "11",
        "dx": { "0": ["J189"], "9": ["486"] },
        "drg": ["193", "194", "195"], "proc": { "0": [], "9": [] }, "services": ["71046"],
    },
    {
        "specialty": "11",
        "dx": { "0": ["N390"], "9": ["5990"] },
        "drg": ["689", "690"], "proc": { "0": [], "9": [] }, "services": ["80053"],
    },
    {
        "specialty": "11",
        "dx": { "0": ["A419"], "9": ["0389"] },
        "drg": ["871", "872"], "proc": { "0": ["5A1945Z"], "9": ["9671"] }, "services": ["80053"],
    },
    {
        "specialty": "20", "surgical": True,
        "dx": { "0": ["S72001A"], "9": ["82000"] },
        "drg": ["480", "481", "482"], "proc": { "0": ["0QS606Z"], "9": ["7935"] }, "services": ["73562"],
    },
]

# Reasons for routine care, which are not treated in the hospital.
ROUTINE_VISIT = {
    "specialty": None,
    "dx": { "0": ["Z0000", "J069", "M5450", "R079"], "9": ["V700", "4659", "7242", "78650"] },
    "services": ["G0439", "90686", "80053"],
}

# Part B services: (type of service, BETOS, lowest paid amount, highest paid amount).
SERVICES = {
    "99213": ("1", "M1B", 60, 110),         # Office visit, established patient
    "99214": ("1", "M1B", 90, 150),         # Office visit, established patient
    "G0439": ("1", "M5D", 100, 140),        # Annual wellness visit
    "90686": ("V", "O1E", 15, 30),          # Influenza vaccine
    "93000": ("5", "T2A", 10, 25),          # Electrocardiogram
    "93306": ("4", "I3B", 150, 250),        # Echocardiogram
    "71046": ("4", "I1A", 20, 40),          # Chest X-ray
    "73562": ("4", "I1D", 25, 50),          # Knee X-ray
    "70551": ("4", "I2C", 180, 300),        # MRI brain
    "77067": ("4", "I1C", 100, 150),        # Screening mammography
    "77427": ("6", "P7A", 150, 220),        # Radiation treatment management
    "83036": ("5", "T1H", 8, 15),           # Hemoglobin A1c
    "82947": ("5", "T1H", 3, 8),            # Glucose
    "80053": ("5", "T1B", 8, 15),           # Comprehensive metabolic panel
    "80061": ("5", "T1B", 10, 20),          # Lipid panel
    "84153": ("5", "T1H", 15, 30),          # Prostate specific antigen
    "85610": ("5", "T1H", 4, 8),            # Prothrombin time
    "94010": ("5", "T2D", 20, 40),          # Spirometry
    "90935": ("1", "P9A", 60, 90),          # Hemodialysis
    "96413": ("1", "O1D", 100, 180),        # Chemotherapy infusion
    "90834": ("T", "M5C", 80, 120),         # Psychotherapy
    "96127": ("1", "M5C", 3, 8),            # Brief emotional assessment
    "96116": ("1", "M5C", 70, 110),         # Neurobehavioral status exam
    "20610": ("2", "P5E", 50, 80),          # Joint injection
}

# DME: (type of service, lowest paid amount, highest paid amount).
DME_SERVICES = {
    "A4253": ("S", 20, 40),                 # Blood glucose test strips
    "E0607": ("P", 30, 50),                 # Home blood glucose monitor
    "E1390": ("R", 80, 150),                # Oxygen concentrator
    "E0570": ("R", 20, 40),                 # Nebulizer
    "E0143": ("P", 60, 100),                # Folding wheeled walker
    "L1833": ("P", 300, 500),               # Knee orthosis
}

# Describes each Part A claim type: (share of Part A claims, facility type,
# service classification, longest stay in days, revenue center codes, lowest
# paid amount, highest paid amount).
PART_A_TYPES = {
    "10": (8, "3", "2", 14, ["0023", "0421", "0551"], 1000, 3000),      # HHA
    "20": (6, "2", "1", 20, ["0022", "0191", "0250"], 5000, 15000),     # SNF
    "30": (1, "1", "8", 20, ["0022", "0120", "0250"], 3000, 9000),      # Swing bed SNF
    "40": (70, "1", "3", 0, ["0250", "0300", "0320", "0450", "0510"], 100, 3000),   # Outpatient
    "50": (0, "8", "1", 31, ["0651"], 3000, 6000),                      # Hospice
    "60": (14, "1", "1", 10, ["0120", "0250", "0300", "0636", "0710"], 8000, 40000),    # Inpatient
    "61": (1, "1", "1", 10, ["0120", "0250", "0300", "0636", "0710"], 8000, 40000),     # Inpatient "Full-Encounter"
}
