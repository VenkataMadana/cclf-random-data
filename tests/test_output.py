import datetime
import importlib
import os
import pickle
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from layouts import LAYOUTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "utils"))
sys.path.insert(0, os.path.join(ROOT, "utils", "reference"))
import caches
from fips_county import get_codes as fips_county_codes
from fips_state import get_abbreviations, get_codes as fips_state_codes
from clinical import ACUTE_EPISODES, CONDITIONS, DME_SERVICES, DRUG_NDCS, ROUTINE_VISIT, SERVICES
from clinical import PART_A_TYPES as PART_A_RULES

PART_A_TYPES = {"10", "20", "30", "40", "50", "60", "61"}
PART_B_TYPES = {"71", "72"}
CLAIM_TYPES = {
    "CCLF1": PART_A_TYPES,
    "CCLF2": PART_A_TYPES,
    "CCLF3": PART_A_TYPES,
    "CCLF4": PART_A_TYPES,
    "CCLF5": PART_B_TYPES,
    "CCLF6": {"81", "82"},
    "CCLF7": {"01", "02", "03"},
    "CCLFA": PART_A_TYPES,
    "CCLFB": PART_B_TYPES,
}
NULL_DATES = {"1000-01-01", "9999-12-31"}
FILE_NAME_IDS = {"A": 4, "F": 3, "D": 4, "K": 4, "C": 4, "P": 6}
MBI = re.compile(r"[1-9][AC-HJKMNP-RT-Y][0-9AC-HJKMNP-RT-Y]\d[AC-HJKMNP-RT-Y][0-9AC-HJKMNP-RT-Y]\d[AC-HJKMNP-RT-Y]{2}\d{2}")


def copy_project(destination):
    ignore = shutil.ignore_patterns(".git", "docs", "tests", "_output", "__pycache__")
    shutil.copytree(ROOT, destination, ignore=ignore)


def generate(directory, seed):
    subprocess.run(
        [sys.executable, "main.py", "--seed", str(seed), "--beneficiaries", "400", "--providers", "300", "--claims", "2000"],
        cwd=directory, check=True, capture_output=True,
    )


def read_tree(directory):
    contents = {}
    for folder, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(folder, file)
            with open(path, "rb") as f:
                contents[os.path.relpath(path, directory)] = f.read()
    return contents


class GeneratedFilesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.mkdtemp()
        cls.project = os.path.join(cls.temp, "project")
        copy_project(cls.project)
        generate(cls.project, seed=1)
        cls.output = os.path.join(cls.project, "_output")
        cls.delivery = os.path.join(cls.output, "240901")

        # Parse each file into one dictionary of field values per record.
        cls.records = {}
        for file_type, layout in LAYOUTS.items():
            with open(os.path.join(cls.output, "cache", f"{file_type}.txt")) as f:
                lines = f.read().splitlines()
            cls.records[file_type] = [
                {name: line[start - 1:end] for name, start, end, _ in layout} | {"_line": line}
                for line in lines
            ]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp)

class OutputTest(GeneratedFilesTest):
    def test_every_file_has_records(self):
        for file_type, records in self.records.items():
            self.assertTrue(records, file_type)

    def test_record_lengths_match_layout(self):
        for file_type, records in self.records.items():
            expected = LAYOUTS[file_type][-1][2]
            for record in records:
                self.assertEqual(len(record["_line"]), expected, file_type)

    def test_fields_match_their_format(self):
        for file_type, records in self.records.items():
            for name, _, _, field_format in LAYOUTS[file_type]:
                amount = re.fullmatch(r"-9\(\d+\)\.(9+)", field_format)
                for record in records:
                    value = record[name]
                    context = f"{file_type} {name}: {value!r}"
                    if field_format == "DATE":
                        datetime.date.fromisoformat(value)
                    elif field_format.startswith("9("):
                        self.assertTrue(value.isdigit(), context)
                    elif amount:
                        self.assertRegex(value, rf"^ *-?\d+\.\d{{{len(amount.group(1))}}}$", context)

    def test_no_placeholder_values_remain(self):
        for file_type, records in self.records.items():
            for record in records:
                self.assertNotIn("?", record["_line"], file_type)

    def test_claim_types_are_valid_for_each_file(self):
        for file_type, valid_types in CLAIM_TYPES.items():
            types = {record["CLM_TYPE_CD"] for record in self.records[file_type]}
            self.assertLessEqual(types, valid_types, file_type)

    def test_claims_have_one_type_across_files(self):
        types = {}
        for file_type in CLAIM_TYPES:
            for record in self.records[file_type]:
                claim_type = types.setdefault(record["CUR_CLM_UNIQ_ID"], record["CLM_TYPE_CD"])
                self.assertEqual(claim_type, record["CLM_TYPE_CD"], file_type)

    def test_claim_families_do_not_overlap(self):
        seen = set()
        for file_type in ("CCLF1", "CCLF5", "CCLF6", "CCLF7"):
            ids = {record["CUR_CLM_UNIQ_ID"] for record in self.records[file_type]}
            self.assertFalse(ids & seen, file_type)
            seen |= ids

    def test_claim_ids_are_unique_in_single_record_files(self):
        for file_type in ("CCLF1", "CCLF7", "CCLFA"):
            ids = [record["CUR_CLM_UNIQ_ID"] for record in self.records[file_type]]
            self.assertEqual(len(ids), len(set(ids)), file_type)

    def test_part_a_and_b_detail_files_cover_the_same_claims(self):
        header_ids = {record["CUR_CLM_UNIQ_ID"] for record in self.records["CCLF1"]}
        for file_type in ("CCLF2", "CCLF4", "CCLFA"):
            ids = {record["CUR_CLM_UNIQ_ID"] for record in self.records[file_type]}
            self.assertEqual(ids, header_ids, file_type)
        part_b_lines = {(r["CUR_CLM_UNIQ_ID"], r["CLM_LINE_NUM"]) for r in self.records["CCLF5"]}
        be_lines = {(r["CUR_CLM_UNIQ_ID"], r["CLM_LINE_NUM"]) for r in self.records["CCLFB"]}
        self.assertEqual(part_b_lines, be_lines)

    def test_claims_have_one_to_five_lines_numbered_from_one(self):
        for file_type in ("CCLF2", "CCLF5", "CCLF6"):
            lines = {}
            for record in self.records[file_type]:
                lines.setdefault(record["CUR_CLM_UNIQ_ID"], []).append(int(record["CLM_LINE_NUM"]))
            for numbers in lines.values():
                self.assertEqual(numbers, list(range(1, len(numbers) + 1)), file_type)
                self.assertLessEqual(len(numbers), 5, file_type)

    def test_part_a_claims_all_have_lines(self):
        header_ids = {record["CUR_CLM_UNIQ_ID"] for record in self.records["CCLF1"]}
        line_ids = {record["CUR_CLM_UNIQ_ID"] for record in self.records["CCLF2"]}
        self.assertEqual(header_ids, line_ids)

    def test_claim_and_line_dates_are_ordered_and_in_the_month(self):
        for file_type in ("CCLF1", "CCLF2", "CCLF5", "CCLF6"):
            for r in self.records[file_type]:
                self.assertLessEqual(r["CLM_FROM_DT"], r["CLM_THRU_DT"], file_type)
                self.assertTrue(r["CLM_FROM_DT"].startswith("2024-08"), file_type)
                self.assertTrue(r["CLM_THRU_DT"].startswith("2024-08"), file_type)
                if "CLM_LINE_FROM_DT" in r:
                    self.assertLessEqual(r["CLM_FROM_DT"], r["CLM_LINE_FROM_DT"], file_type)
                    self.assertLessEqual(r["CLM_LINE_FROM_DT"], r["CLM_LINE_THRU_DT"], file_type)
                    self.assertLessEqual(r["CLM_LINE_THRU_DT"], r["CLM_THRU_DT"], file_type)

    def test_no_claims_after_death(self):
        deaths = {
            r["BENE_MBI_ID"]: r["BENE_DEATH_DT"]
            for r in self.records["CCLF8"]
            if r["BENE_DEATH_DT"] not in NULL_DATES
        }
        self.assertTrue(deaths)
        for file_type in ("CCLF1", "CCLF5", "CCLF6"):
            for r in self.records[file_type]:
                if r["BENE_MBI_ID"] in deaths:
                    self.assertLessEqual(r["CLM_THRU_DT"], deaths[r["BENE_MBI_ID"]], file_type)

    def test_claims_reference_known_beneficiaries(self):
        mbis = {r["BENE_MBI_ID"] for r in self.records["CCLF8"]}
        for file_type in CLAIM_TYPES:
            for r in self.records[file_type]:
                self.assertIn(r["BENE_MBI_ID"], mbis, file_type)

    def test_icd_version_matches_the_service_dates(self):
        for file_type in ("CCLF1", "CCLF3", "CCLF4", "CCLF5"):
            versions = {r["DGNS_PRCDR_ICD_IND"] for r in self.records[file_type]}
            self.assertEqual(versions, {"0"}, file_type)

    def test_procedure_file_uses_procedure_codes(self):
        reasons = list(CONDITIONS.values()) + ACUTE_EPISODES
        valid = {code for reason in reasons for code in reason["proc"]["0"]}
        self.assertTrue(self.records["CCLF3"])
        for r in self.records["CCLF3"]:
            self.assertIn(r["CLM_PRCDR_CD"].strip(), valid)

    def test_paid_amounts_have_two_decimals_in_cclf2(self):
        for r in self.records["CCLF2"]:
            self.assertRegex(r["CLM_LINE_CVRD_PD_AMT"], r"\.\d{2}$")

    def test_provider_state_codes_are_fips(self):
        valid = set(fips_state_codes())
        for r in self.records["CCLF1"]:
            self.assertIn(r["PRVDR_FAC_FIPS_ST_CD"], valid)
        for r in self.records["CCLF5"]:
            self.assertIn(r["RNDRG_PRVDR_FIPS_ST_CD"], valid)

    def test_beneficiary_demographics(self):
        records = self.records["CCLF8"]
        self.assertLessEqual({r["BENE_SEX_CD"] for r in records}, {"0", "1", "2"})
        self.assertLessEqual({"1", "2"}, {r["BENE_SEX_CD"] for r in records})
        counties = {}
        states = iter(fips_state_codes())
        for code in fips_county_codes():
            if code == "000":
                state = next(states)
                counties[state] = set()
            else:
                counties[state].add(code)
        for r in records:
            self.assertRegex(r["BENE_MBI_ID"], MBI)
            state = r["BENE_FIPS_STATE_CD"]
            self.assertEqual(get_abbreviations()[state], r["GEO_USPS_STATE_CD"])
            self.assertIn(r["BENE_FIPS_CNTY_CD"], counties[state])
            self.assertEqual(r["BENE_ZIP_CD"], r["GEO_ZIP5_CD"])

    def test_mbis_use_the_full_alphanumeric_range(self):
        for position in (2, 5):
            characters = {r["BENE_MBI_ID"][position] for r in self.records["CCLF8"]}
            self.assertTrue(characters & set("0123456789"), position)
            self.assertTrue(characters - set("AN0123456789"), position)

    def test_not_all_beneficiaries_are_deceased_or_in_hospice(self):
        records = self.records["CCLF8"]
        self.assertTrue(any(r["BENE_DEATH_DT"] in NULL_DATES for r in records))
        self.assertTrue(any(r["BENE_RNG_BGN_DT"] in NULL_DATES for r in records))

    def test_enrollment_dates_are_ordered(self):
        for r in self.records["CCLF8"]:
            self.assertLess(r["BENE_DOB"], r["BENE_PART_A_ENRLMT_BGN_DT"])
            self.assertLessEqual(r["BENE_PART_A_ENRLMT_BGN_DT"], r["BENE_PART_B_ENRLMT_BGN_DT"])
            self.assertLessEqual(r["BENE_PART_B_ENRLMT_BGN_DT"], "2024-08-01")
            self.assertLessEqual(r["BENE_RNG_BGN_DT"], r["BENE_RNG_END_DT"])

    def test_age_matches_date_of_birth(self):
        for r in self.records["CCLF8"]:
            as_of = "2024-08-31" if r["BENE_DEATH_DT"] in NULL_DATES else r["BENE_DEATH_DT"]
            dob = datetime.date.fromisoformat(r["BENE_DOB"])
            end = datetime.date.fromisoformat(as_of)
            age = end.year - dob.year - ((end.month, end.day) < (dob.month, dob.day))
            self.assertEqual(int(r["BENE_AGE"]), age)

    def test_xref_lists_real_mbi_changes(self):
        mbis = {r["BENE_MBI_ID"] for r in self.records["CCLF8"]}
        self.assertLess(len(self.records["CCLF9"]), len(mbis))
        for r in self.records["CCLF9"]:
            self.assertIn(r["CRNT_NUM"], mbis)
            self.assertRegex(r["PRVS_NUM"], MBI)
            self.assertNotEqual(r["CRNT_NUM"], r["PRVS_NUM"])
            self.assertLessEqual(r["PRVS_ID_EFCTV_DT"], r["PRVS_ID_OBSLT_DT"])

    def test_effective_dates_fall_between_service_and_file_dates(self):
        for file_type in ("CCLF1", "CCLF5", "CCLF6"):
            for r in self.records[file_type]:
                self.assertLessEqual(r["CLM_THRU_DT"], r["CLM_EFCTV_DT"], file_type)
                self.assertLessEqual(r["CLM_EFCTV_DT"], "2024-09-01", file_type)
                self.assertEqual(r["CLM_EFCTV_DT"], r["CLM_IDR_LD_DT"], file_type)

    def test_claims_have_one_adjustment_type(self):
        for file_type in ("CCLF5", "CCLF6"):
            types = {}
            for r in self.records[file_type]:
                adjustment = types.setdefault(r["CUR_CLM_UNIQ_ID"], r["CLM_ADJSMT_TYPE_CD"])
                self.assertEqual(adjustment, r["CLM_ADJSMT_TYPE_CD"], file_type)
            # DME is a small share of claims, so a run may not have every type.
            found = {a.strip() for a in types.values()}
            self.assertLessEqual(found, {"0", "1", "2"}, file_type)
            if file_type == "CCLF5":
                self.assertEqual(found, {"0", "1", "2"})

    def test_part_a_cancellations_net_against_their_originals(self):
        related = {}
        for r in self.records["CCLF1"]:
            key = (r["CLM_BLG_PRVDR_OSCAR_NUM"], r["CLM_FROM_DT"], r["CLM_THRU_DT"], r["BENE_MBI_ID"])
            related.setdefault(key, []).append(r)
        self.check_cancellations(related, "CLM_PMT_AMT")

    def test_part_b_and_dme_cancellations_net_against_their_originals(self):
        for file_type in ("CCLF5", "CCLF6"):
            related = {}
            for r in self.records[file_type]:
                key = (r["CLM_CNTL_NUM"], r["BENE_MBI_ID"], r["CLM_LINE_NUM"])
                related.setdefault(key, []).append(r)
            self.check_cancellations(related, "CLM_LINE_CVRD_PD_AMT", required=file_type == "CCLF5")

    def check_cancellations(self, related, amount_field, required=True):
        cancellations = 0
        for records in related.values():
            by_type = {}
            for r in records:
                by_type.setdefault(r["CLM_ADJSMT_TYPE_CD"].strip(), []).append(r)
            for cancellation in by_type.get("1", []):
                cancellations += 1
                self.assertIn("0", by_type)
                # Separate visits can share a natural key, so one must match.
                self.assertTrue(any(
                    float(cancellation[amount_field]) == float(original[amount_field])
                    and original["CLM_EFCTV_DT"] <= cancellation["CLM_EFCTV_DT"]
                    for original in by_type["0"]
                ))
        if required:
            self.assertTrue(cancellations)

    def test_part_a_files_share_the_natural_key(self):
        headers = {r["CUR_CLM_UNIQ_ID"]: r for r in self.records["CCLF1"]}
        for file_type in ("CCLF3", "CCLF4"):
            for r in self.records[file_type]:
                header = headers[r["CUR_CLM_UNIQ_ID"]]
                for field in ("CLM_BLG_PRVDR_OSCAR_NUM", "CLM_FROM_DT", "CLM_THRU_DT", "BENE_MBI_ID"):
                    self.assertEqual(r[field], header[field], file_type)

    def test_paid_amounts_are_not_signed(self):
        for file_type, field in (("CCLF1", "CLM_PMT_AMT"), ("CCLF5", "CLM_LINE_CVRD_PD_AMT"), ("CCLF6", "CLM_LINE_CVRD_PD_AMT")):
            for r in self.records[file_type]:
                self.assertGreaterEqual(float(r[field]), 0, file_type)

    def test_part_d_claim_types_match_adjustments(self):
        adjustments = {"01": "0", "02": "2", "03": "1"}
        records = self.records["CCLF7"]
        self.assertEqual({r["CLM_TYPE_CD"] for r in records}, set(adjustments))
        for r in records:
            self.assertEqual(r["CLM_ADJSMT_TYPE_CD"].strip(), adjustments[r["CLM_TYPE_CD"]])
            deleted = r["CLM_TYPE_CD"] == "03"
            self.assertEqual(r["CLM_LINE_NDC_CD"].strip() == "", deleted)
            self.assertEqual(float(r["CLM_LINE_BENE_PMT_AMT"]) == 0, deleted)

    def test_betos_codes_are_betos(self):
        for r in self.records["CCLF5"]:
            self.assertRegex(r["HCPCS_BETOS_CD"], r"^[A-Z]\d[A-Z]$")

    def test_claim_count_matches_the_request(self):
        ids = set()
        for file_type in ("CCLF1", "CCLF5", "CCLF6", "CCLF7"):
            ids |= {r["CUR_CLM_UNIQ_ID"] for r in self.records[file_type]}
        self.assertEqual(len(ids), 2000)

    def test_file_names_follow_the_conventions(self):
        ids = {}
        for file_type in list(LAYOUTS) + ["CCLF0"]:
            names = os.listdir(os.path.join(self.delivery, file_type))
            self.assertEqual(len(names), 9, file_type)
            for name in names:
                match = re.fullmatch(rf"P\.([AFDKCP])(\d+)\.ACO\.ZC{file_type[-1]}([YR])24\.D240901\.T\d{{7}}", name)
                self.assertIsNotNone(match, name)
                model, entity, run = match.groups()
                self.assertEqual(len(entity), FILE_NAME_IDS[model], name)
                self.assertTrue(run == "Y" or model in "AFD", name)
                self.assertEqual(ids.setdefault(model, entity), entity, name)

    def test_summary_file_reports_real_counts(self):
        folder = os.path.join(self.delivery, "CCLF0")
        for name in os.listdir(folder):
            with open(os.path.join(folder, name)) as f:
                lines = f.read().splitlines()
            self.assertEqual(lines[0], f"{'File Number':13}|{'File Description':20}|{'Total Records Count':20}|{'Record Length':13}")
            if not name.startswith(("P.A", "P.F", "P.P")):
                self.assertEqual(len(lines), 1, name)
                continue
            self.assertEqual(len(lines), 1 + len(LAYOUTS), name)
            for line in lines[1:]:
                self.assertEqual(len(line), 70, line)
                file_type, description, count, length = line.split("|")
                file_type = file_type.strip()
                self.assertTrue(description.strip().endswith("File."), line)
                self.assertEqual(int(count), len(self.records[file_type]), line)
                self.assertEqual(int(length), LAYOUTS[file_type][-1][2], line)

    def test_delivered_files_match_generated_data(self):
        for file_type, records in self.records.items():
            folder = os.path.join(self.delivery, file_type)
            for name in os.listdir(folder):
                with open(os.path.join(folder, name)) as f:
                    self.assertEqual(f.read().splitlines(), [r["_line"] for r in records], name)


class CorrelationTest(GeneratedFilesTest):
    """Checks that a patient's claims and codes relate to each other."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(os.path.join(cls.output, "cache", "beneficiaries.pkl"), "rb") as f:
            cls.benes = pickle.load(f)
        with open(os.path.join(cls.output, "cache", "providers.pkl"), "rb") as f:
            cls.providers = pickle.load(f)
        cls.headers = {r["CUR_CLM_UNIQ_ID"]: r for r in cls.records["CCLF1"]}

    def patient_dx(self, mbi):
        bene = self.benes[mbi]
        return {
            CONDITIONS[name]["dx"]["0"][index % len(CONDITIONS[name]["dx"]["0"])]
            for name, index in bene["conditions"].items()
        }

    def test_values_are_in_the_reference_tables(self):
        fields = [
            ("CCLF1", "CLM_BILL_FAC_TYPE_CD", "claim_bill_facility_type"),
            ("CCLF1", "CLM_BILL_CLSFCTN_CD", "claim_service_classification_type"),
            ("CCLF1", "BENE_PTNT_STUS_CD", "ffs_patient_discharge"),
            ("CCLF1", "CLM_OP_SRVC_TYPE_CD", "claim_outpatient_service_type"),
            ("CCLF1", "CLM_ADMSN_TYPE_CD", "claim_admission_type"),
            ("CCLF1", "CLM_ADMSN_SRC_CD", "claim_source_inpatient_admission"),
            ("CCLF1", "CLM_BILL_FREQ_CD", "claim_frequency"),
            ("CCLF1", "CLM_QUERY_CD", "claim_query"),
            ("CCLF1", "CLM_MDCR_NPMT_RSN_CD", "reason_payment"),
            ("CCLF1", "CLM_NCH_PRMRY_PYR_CD", "nhc_primary_payer"),
            ("CCLF2", "CLM_LINE_PROD_REV_CTR_CD", "revenue_code"),
            ("CCLF2", "HCPCS_1_MDFR_CD", "hcpcs_mod"),
            ("CCLF4", "CLM_PROD_TYPE_CD", "claim_product_type"),
            ("CCLF4", "CLM_POA_IND", "present_on_admission"),
            ("CCLF5", "RNDRG_PRVDR_TYPE_CD", "rendering_provider_type"),
            ("CCLF5", "CLM_PRVDR_SPCLTY_CD", "provider_specialty"),
            ("CCLF5", "CLM_FED_TYPE_SRVC_CD", "type_service"),
            ("CCLF5", "CLM_POS_CD", "place_of_service"),
            ("CCLF5", "CLM_LINE_PRMRY_PYR_CD", "primary_payer"),
            ("CCLF5", "CLM_CARR_PMT_DNL_CD", "carrier_payment_denial"),
            ("CCLF5", "CLM_PRCSG_IND_CD", "processing_indicator"),
            ("CCLF5", "CLM_DISP_CD", "claim_disposition"),
            ("CCLF6", "CLM_FED_TYPE_SRVC_CD", "type_service"),
            ("CCLF7", "PRVDR_SRVC_ID__QLFYR_CD", "provider_service_identifier_qualifier"),
            ("CCLF7", "CLM_DSPNSNG_STUS_CD", "claim_dispensing"),
            ("CCLF7", "CLM_DAW_PROD_SLCTN_CD", "daw_product_selection"),
            ("CCLF7", "CLM_PHRMCY_SRVC_TYPE_CD", "pharmacy_service_type"),
            ("CCLF8", "BENE_RACE_CD", "beneficiary_race"),
            ("CCLF8", "BENE_MDCR_STUS_CD", "beneficiary_medicare_status"),
            ("CCLF8", "BENE_DUAL_STUS_CD", "beneficiary_dual_status"),
            ("CCLF8", "BENE_ORGNL_ENTLMT_RSN_CD", "beneficiary_original_entitlement_reason_code"),
            ("CCLF8", "BENE_ENTLMT_BUYIN_IND", "beneficiary_entitlement_buy_in_indicator"),
        ]
        for file_type, field, module in fields:
            valid = {str(code).strip() for code in importlib.import_module(module).get_codes()}
            for r in self.records[file_type]:
                value = r[field].strip()
                if value:
                    self.assertIn(value, valid, f"{file_type} {field}")

    def test_principal_diagnosis_matches_across_files(self):
        first = {r["CUR_CLM_UNIQ_ID"]: r for r in self.records["CCLF4"] if r["CLM_VAL_SQNC_NUM"] == "01"}
        for claim_id, header in self.headers.items():
            self.assertEqual(first[claim_id]["CLM_DGNS_CD"], header["PRNCPL_DGNS_CD"])

    def test_secondary_diagnoses_are_the_patients_conditions(self):
        for r in self.records["CCLF4"]:
            if r["CLM_VAL_SQNC_NUM"] != "01":
                self.assertIn(r["CLM_DGNS_CD"].strip(), self.patient_dx(r["BENE_MBI_ID"]))

    def test_part_b_diagnoses_are_filled_from_the_first_slot(self):
        for r in self.records["CCLF5"]:
            self.assertEqual(r["CLM_LINE_DGNS_CD"].strip(), r["CLM_DGNS_1_CD"].strip())
            slots = [r[f"CLM_DGNS_{i}_CD"].strip() for i in range(1, 13)]
            used = [code for code in slots if code]
            self.assertEqual(slots[:len(used)], used)

    def test_conditions_fit_sex_and_age(self):
        for bene in self.benes.values():
            for name in bene["conditions"]:
                condition = CONDITIONS[name]
                self.assertEqual(condition.get("sex", bene["gender"]), bene["gender"], name)
                self.assertGreaterEqual(int(bene["age"]) + 1, condition.get("min_age", 0), name)

    def test_sex_specific_diagnoses_fit_the_patient(self):
        for file_type, field in (("CCLF1", "PRNCPL_DGNS_CD"), ("CCLF4", "CLM_DGNS_CD"), ("CCLF5", "CLM_LINE_DGNS_CD")):
            for r in self.records[file_type]:
                code = r[field].strip()
                sex = self.benes[r["BENE_MBI_ID"]]["gender"]
                if code == "C61":
                    self.assertEqual(sex, "1", file_type)
                if code.startswith("C50"):
                    self.assertEqual(sex, "2", file_type)

    def test_only_inpatient_claims_have_inpatient_fields(self):
        for r in self.headers.values():
            inpatient = r["CLM_TYPE_CD"] in ("60", "61")
            self.assertEqual(bool(r["DGNS_DRG_CD"].strip()), inpatient)
            self.assertEqual(bool(r["ADMTG_DGNS_CD"].strip()), inpatient)
            if r["CLM_TYPE_CD"] == "40":
                self.assertEqual(r["CLM_ADMSN_TYPE_CD"].strip(), "")
                self.assertEqual(r["CLM_ADMSN_SRC_CD"].strip(), "")
            if not inpatient:
                for field in ("CLM_OPRTNL_IME_AMT", "CLM_OPRTNL_DSPRPRTNT_AMT"):
                    self.assertEqual(float(r[field]), 0)
        for r in self.records["CCLF3"]:
            self.assertIn(r["CLM_TYPE_CD"], ("60", "61"))
        for r in self.records["CCLF4"]:
            self.assertEqual(bool(r["CLM_POA_IND"].strip()), r["CLM_TYPE_CD"] in ("60", "61"))

    def test_drg_and_procedure_fit_the_principal_diagnosis(self):
        reasons = list(CONDITIONS.values()) + ACUTE_EPISODES
        procedures = {r["CUR_CLM_UNIQ_ID"]: r["CLM_PRCDR_CD"].strip() for r in self.records["CCLF3"]}
        inpatient = [r for r in self.headers.values() if r["DGNS_DRG_CD"].strip()]
        self.assertTrue(inpatient)
        for r in inpatient:
            matches = [reason for reason in reasons if r["PRNCPL_DGNS_CD"].strip() in reason["dx"]["0"]]
            self.assertTrue(matches)
            self.assertTrue(any(r["DGNS_DRG_CD"].strip() in reason["drg"] for reason in matches))
            if r["CUR_CLM_UNIQ_ID"] in procedures:
                self.assertTrue(any(procedures[r["CUR_CLM_UNIQ_ID"]] in reason["proc"]["0"] for reason in matches))

    def test_bill_type_follows_claim_type(self):
        bill_types = {
            "10": ("3", "2"), "20": ("2", "1"), "30": ("1", "8"), "40": ("1", "3"),
            "50": ("8", "1"), "60": ("1", "1"), "61": ("1", "1"),
        }
        for r in self.headers.values():
            self.assertEqual((r["CLM_BILL_FAC_TYPE_CD"], r["CLM_BILL_CLSFCTN_CD"]), bill_types[r["CLM_TYPE_CD"]])

    def test_revenue_and_service_codes_follow_claim_type(self):
        for r in self.records["CCLF2"]:
            self.assertIn(r["CLM_LINE_PROD_REV_CTR_CD"], PART_A_RULES[r["CLM_TYPE_CD"]][4])
            self.assertEqual(bool(r["CLM_LINE_HCPCS_CD"].strip()), r["CLM_TYPE_CD"] == "40")
            if r["CLM_REV_APC_HIPPS_CD"].strip():
                self.assertIn(r["CLM_TYPE_CD"], ("10", "20", "30"))
        for r in self.records["CCLF5"]:
            tos, betos, _, _ = SERVICES[r["CLM_LINE_HCPCS_CD"].strip()]
            self.assertEqual(r["CLM_FED_TYPE_SRVC_CD"], tos)
            self.assertEqual(r["HCPCS_BETOS_CD"], betos)
        for r in self.records["CCLF6"]:
            self.assertEqual(r["CLM_FED_TYPE_SRVC_CD"], DME_SERVICES[r["CLM_LINE_HCPCS_CD"].strip()][0])

    def test_adjustment_codes_agree(self):
        expected = {"0": ("1", "3"), "1": ("8", "0"), "2": ("7", "5")}
        for r in self.headers.values():
            self.assertEqual((r["CLM_BILL_FREQ_CD"], r["CLM_QUERY_CD"]), expected[r["CLM_ADJSMT_TYPE_CD"].strip()])
        dispositions = {"0": "01", "1": "03", "2": "02"}
        for r in self.records["CCLF5"]:
            self.assertEqual(r["CLM_DISP_CD"], dispositions[r["CLM_ADJSMT_TYPE_CD"].strip()])

    def test_hospice_claims_are_for_enrolled_patients(self):
        claims = [r for r in self.headers.values() if r["CLM_TYPE_CD"] == "50"]
        self.assertTrue(claims)
        terminal = {code for c in CONDITIONS.values() if c.get("terminal") for code in c["dx"]["0"]}
        for r in claims:
            bene = self.benes[r["BENE_MBI_ID"]]
            self.assertLessEqual(bene["hospice_bgn"], r["CLM_FROM_DT"])
            self.assertNotEqual(bene["hospice_bgn"], "1000-01-01")
            self.assertIn(r["PRNCPL_DGNS_CD"].strip(), terminal)

    def test_medicare_status_follows_age_and_esrd(self):
        for bene in self.benes.values():
            age = int(bene["age"])
            self.assertEqual(bene["mdcr_status"][0], "1" if age >= 65 else "2")
            self.assertEqual(bene["mdcr_status"][1], "1" if "esrd" in bene["conditions"] else "0")

    def test_discharge_status_reports_deaths_on_the_date_of_death(self):
        expired = 0
        for r in self.headers.values():
            dod = self.benes[r["BENE_MBI_ID"]]["dod"]
            if r["BENE_PTNT_STUS_CD"].strip() in ("20", "40"):
                expired += 1
                self.assertEqual(r["CLM_THRU_DT"], dod)
            elif r["CLM_THRU_DT"] == dod:
                self.fail(r["CUR_CLM_UNIQ_ID"])
        self.assertTrue(expired)

    def test_part_d_drugs_are_the_patients_regular_drugs(self):
        seen = set()
        for r in self.records["CCLF7"]:
            ndc = r["CLM_LINE_NDC_CD"].strip()
            if not ndc:
                continue
            valid = {DRUG_NDCS[drug] for drug in self.benes[r["BENE_MBI_ID"]]["drugs"]}
            self.assertIn(ndc, valid)
            self.assertNotIn((r["BENE_MBI_ID"], ndc), seen)
            seen.add((r["BENE_MBI_ID"], ndc))

    def test_every_drug_comes_from_a_condition(self):
        for bene in self.benes.values():
            valid = {drug for name in bene["conditions"] for drug in CONDITIONS[name]["drugs"]}
            self.assertLessEqual(set(bene["drugs"]), valid)

    def test_dme_claims_fit_the_patients_conditions(self):
        for r in self.records["CCLF6"]:
            valid = {code for name in self.benes[r["BENE_MBI_ID"]]["conditions"] for code in CONDITIONS[name]["dme"]}
            self.assertIn(r["CLM_LINE_HCPCS_CD"].strip(), valid)

    def test_care_is_local(self):
        total = local = 0
        for r in self.headers.values():
            total += 1
            local += r["PRVDR_FAC_FIPS_ST_CD"] == self.benes[r["BENE_MBI_ID"]]["fips_state"]
        self.assertGreater(local / total, 0.9)

    def test_patients_keep_a_regular_doctor(self):
        pcp_visits = 0
        for r in self.records["CCLF5"]:
            bene = self.benes[r["BENE_MBI_ID"]]
            self.assertEqual(r["CLM_RFRG_PRVDR_NPI_NUM"], bene["pcp"])
            self.assertIn(r["CLM_RNDRG_PRVDR_NPI_NUM"], [bene["pcp"], *bene["specialists"].values()])
            pcp_visits += r["CLM_RNDRG_PRVDR_NPI_NUM"] == bene["pcp"]
        self.assertGreater(pcp_visits / len(self.records["CCLF5"]), 0.5)

    def test_provider_specialty_matches_role(self):
        for bene in self.benes.values():
            for specialty, npi in bene["specialists"].items():
                self.assertEqual(self.providers[npi]["role"], "specialist")
                self.assertEqual(self.providers[npi]["psc"], specialty)

    def test_utilization_is_skewed_toward_sicker_patients(self):
        counts = dict.fromkeys(self.benes, 0)
        for file_type in ("CCLF1", "CCLF7"):
            for r in self.records[file_type]:
                counts[r["BENE_MBI_ID"]] += 1
        for file_type in ("CCLF5", "CCLF6"):
            seen = {(r["CUR_CLM_UNIQ_ID"], r["BENE_MBI_ID"]) for r in self.records[file_type]}
            for _, mbi in seen:
                counts[mbi] += 1
        ordered = sorted(counts.values(), reverse=True)
        self.assertGreater(sum(ordered[:len(ordered) // 10]) / sum(ordered), 0.3)
        self.assertLess(statistics.median(ordered), statistics.mean(ordered))
        self.assertLessEqual(ordered[0], 50)
        healthy = [counts[m] for m, b in self.benes.items() if not b["conditions"]]
        sick = [counts[m] for m, b in self.benes.items() if len(b["conditions"]) >= 3]
        self.assertGreater(statistics.mean(sick), 2 * statistics.mean(healthy))

    def test_part_a_lines_add_up_to_the_claim(self):
        totals = {}
        for r in self.records["CCLF2"]:
            totals[r["CUR_CLM_UNIQ_ID"]] = totals.get(r["CUR_CLM_UNIQ_ID"], 0) + float(r["CLM_LINE_CVRD_PD_AMT"])
        for claim_id, header in self.headers.items():
            self.assertAlmostEqual(totals[claim_id], float(header["CLM_PMT_AMT"]), places=2)

    def test_amounts_are_ordered(self):
        for r in self.records["CCLF5"]:
            self.assertGreaterEqual(float(r["CLM_LINE_ALOWD_CHRG_AMT"]), float(r["CLM_LINE_CVRD_PD_AMT"]))
        for r in self.headers.values():
            self.assertGreaterEqual(float(r["CLM_MDCR_INSTNL_TOT_CHRG_AMT"]), float(r["CLM_PMT_AMT"]))

    def test_no_excluded_substance_abuse_codes(self):
        reasons = list(CONDITIONS.values()) + ACUTE_EPISODES
        for reason in reasons:
            for code in reason["dx"]["0"]:
                self.assertNotRegex(code, r"^F1[0-9]")
            for code in reason["dx"]["9"]:
                self.assertNotRegex(code, r"^(291|292|303|304|305)")
            self.assertFalse(set(reason["drg"]) & {"522", "523", "895", "896", "897"})


class RelatedClaimsTest(unittest.TestCase):
    def test_related_claims_do_not_exceed_the_quantity(self):
        claims = []
        with mock.patch.multiple(caches, claims=claims, cancellation_rate=1, readjustment_rate=1, first_claim_weights=[1, 0],
                                 family_weights={"A": 1}, beneficiaries={}, providers={}, provider_pools={}, market_states=[]):
            caches.choose_market()
            caches.generate_providers(5)
            caches.generate_beneficiaries(5, 2024, 8)
            caches.generate_claims(2, 2024, 8)
        self.assertEqual([claim["adj"] for claim in claims], ["0", "1"])


class RunTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp)

    def test_same_seed_generates_identical_files(self):
        first = os.path.join(self.temp, "first")
        second = os.path.join(self.temp, "second")
        third = os.path.join(self.temp, "third")
        for directory, seed in ((first, 5), (second, 5), (third, 6)):
            copy_project(directory)
            generate(directory, seed)

        def outputs(directory):
            # Pickles can differ in bytes for equal data, so compare the text files.
            tree = read_tree(os.path.join(directory, "_output"))
            return {path: data for path, data in tree.items() if not path.endswith(".pkl")}

        self.assertEqual(outputs(first), outputs(second))
        self.assertNotEqual(outputs(first), outputs(third))

    def test_december_claims_keep_their_year_in_file_names(self):
        project = os.path.join(self.temp, "project")
        copy_project(project)
        path = os.path.join(project, "main.py")
        with open(path) as f:
            source = f.read()
        self.assertIn("claims_month = 8\n", source)
        with open(path, "w") as f:
            f.write(source.replace("claims_month = 8\n", "claims_month = 12\n"))
        generate(project, seed=1)
        for name in os.listdir(os.path.join(project, "_output", "250101", "CCLF1")):
            self.assertRegex(name, r"\.ZC1[YR]24\.D250101\.")

    def test_small_populations_generate_files(self):
        project = os.path.join(self.temp, "project")
        copy_project(project)
        subprocess.run(
            [sys.executable, "main.py", "--seed", "1", "--beneficiaries", "1", "--providers", "1", "--claims", "3"],
            cwd=project, check=True, capture_output=True,
        )
        self.assertTrue(os.path.exists(os.path.join(project, "_output", "240901", "CCLF0")))

    def test_claims_before_icd10_use_icd9_codes(self):
        project = os.path.join(self.temp, "project")
        copy_project(project)
        path = os.path.join(project, "main.py")
        with open(path) as f:
            source = f.read()
        self.assertIn("claims_year = 2024\n", source)
        with open(path, "w") as f:
            f.write(source.replace("claims_year = 2024\n", "claims_year = 2014\n"))
        generate(project, seed=1)
        layout = {name: (start, end) for name, start, end, _ in LAYOUTS["CCLF1"]}
        icd9 = {code for reason in list(CONDITIONS.values()) + ACUTE_EPISODES + [ROUTINE_VISIT] for code in reason["dx"]["9"]}
        with open(os.path.join(project, "_output", "cache", "CCLF1.txt")) as f:
            for line in f:
                start, end = layout["PRNCPL_DGNS_CD"]
                self.assertIn(line[start - 1:end].strip(), icd9)
                self.assertEqual(line[layout["DGNS_PRCDR_ICD_IND"][0] - 1], "9")

    def test_main_fails_when_a_script_fails(self):
        project = os.path.join(self.temp, "project")
        copy_project(project)
        with open(os.path.join(project, "cclf_3.py"), "w") as f:
            f.write("raise RuntimeError('broken')\n")
        with self.assertRaises(subprocess.CalledProcessError):
            generate(project, seed=1)
        self.assertFalse(os.path.exists(os.path.join(project, "_output", "240901", "CCLF4")))


if __name__ == "__main__":
    unittest.main()
