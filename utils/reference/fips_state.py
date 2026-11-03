# FIPS State Codes
# https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt
def get_codes():
    return [
		"01",     # ALABAMA
		"02",     # ALASKA
		"04",     # ARIZONA
		"05",     # ARKANSAS
		"06",     # CALIFORNIA
		"08",     # COLORADO
		"09",     # CONNECTICUT
		"10",     # DELAWARE
		"11",     # DISTRICT OF COLUMBIA
		"12",     # FLORIDA
		"13",     # GEORGIA
		"15",     # HAWAII
		"16",     # IDAHO
		"17",     # ILLINOIS
		"18",     # INDIANA
		"19",     # IOWA
		"20",     # KANSAS
		"21",     # KENTUCKY
		"22",     # LOUISIANA
		"23",     # MAINE
		"24",     # MARYLAND
		"25",     # MASSACHUSETTS
		"26",     # MICHIGAN
		"27",     # MINNESOTA
		"28",     # MISSISSIPPI
		"29",     # MISSOURI
		"30",     # MONTANA
		"31",     # NEBRASKA
		"32",     # NEVADA
		"33",     # NEW HAMPSHIRE
		"34",     # NEW JERSEY
		"35",     # NEW MEXICO
		"36",     # NEW YORK
		"37",     # NORTH CAROLINA
		"38",     # NORTH DAKOTA
		"39",     # OHIO
		"40",     # OKLAHOMA
		"41",     # OREGON
		"42",     # PENNSYLVANIA
		"44",     # RHODE ISLAND
		"45",     # SOUTH CAROLINA
		"46",     # SOUTH DAKOTA
		"47",     # TENNESSEE
		"48",     # TEXAS
		"49",     # UTAH
		"50",     # VERMONT
		"51",     # VIRGINIA
		"53",     # WASHINGTON
		"54",     # WEST VIRGINIA
		"55",     # WISCONSIN
		"56",     # WYOMING        
	]

# USPS state abbreviations by FIPS state code.
def get_abbreviations():
    return {
        "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
        "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
        "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
        "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
        "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
        "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
        "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
        "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
        "54": "WV", "55": "WI", "56": "WY",
    }
