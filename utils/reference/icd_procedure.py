# Sample ICD-9-CM and ICD-10-PCS procedure codes. No decimal.
# Excludes the alcohol and substance abuse codes in Appendix A of the PDF because
# CMS removes those claims from the CCLFs.
def get_codes():
    return [
        { "code": "4701", "ver": "9" },         # Laparoscopic appendectomy
        { "code": "5123", "ver": "9" },         # Laparoscopic cholecystectomy
        { "code": "8154", "ver": "9" },         # Total knee replacement
        { "code": "9671", "ver": "9" },         # Mechanical ventilation, less than 96 hours
        { "code": "3995", "ver": "9" },         # Hemodialysis
        { "code": "9904", "ver": "9" },         # Transfusion of packed cells
        { "code": "0DTJ4ZZ", "ver": "0" },      # Resection of appendix, percutaneous endoscopic
        { "code": "0FT44ZZ", "ver": "0" },      # Resection of gallbladder, percutaneous endoscopic
        { "code": "0SRC0J9", "ver": "0" },      # Replacement of right knee joint, cemented, open
        { "code": "5A1945Z", "ver": "0" },      # Respiratory ventilation, 24-96 consecutive hours
        { "code": "5A1D70Z", "ver": "0" },      # Hemodialysis, intermittent, less than 6 hours per day
        { "code": "30233N1", "ver": "0" },      # Transfusion of red blood cells, peripheral vein
    ]
