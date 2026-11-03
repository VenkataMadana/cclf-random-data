import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from layouts import LAYOUTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "utils", "reference"))
from fips_county import get_codes as fips_county_codes
from fips_state import get_abbreviations, get_codes as fips_state_codes
from icd_procedure import get_codes as procedure_codes

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
        [sys.executable, "main.py", "--seed", str(seed), "--beneficiaries", "200", "--providers", "100", "--claims", "1000"],
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


class OutputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.mkdtemp()
        cls.project = os.path.join(cls.temp, "project")
        copy_project(cls.project)
        generate(cls.project, seed=1)
        cls.output = os.path.join(cls.project, "_output")
        cls.delivery = os.path.join(cls.output, "240801")

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
        for file_type in ("CCLF1", "CCLF3", "CCLF4", "CCLF7", "CCLFA"):
            ids = [record["CUR_CLM_UNIQ_ID"] for record in self.records[file_type]]
            self.assertEqual(len(ids), len(set(ids)), file_type)

    def test_part_a_and_b_detail_files_cover_the_same_claims(self):
        header_ids = {record["CUR_CLM_UNIQ_ID"] for record in self.records["CCLF1"]}
        for file_type in ("CCLF2", "CCLF3", "CCLF4", "CCLFA"):
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
        valid = {code["code"] for code in procedure_codes() if code["ver"] == "0"}
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
        self.assertEqual({r["BENE_SEX_CD"] for r in records}, {"0", "1", "2"})
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

    def test_file_names_follow_the_conventions(self):
        ids = {}
        for file_type in list(LAYOUTS) + ["CCLF0"]:
            names = os.listdir(os.path.join(self.delivery, file_type))
            self.assertEqual(len(names), 9, file_type)
            for name in names:
                match = re.fullmatch(rf"P\.([AFDKCP])(\d+)\.ACO\.ZC{file_type[-1]}([YR])24\.D240801\.T\d{{7}}", name)
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

    def test_main_fails_when_a_script_fails(self):
        project = os.path.join(self.temp, "project")
        copy_project(project)
        with open(os.path.join(project, "cclf_3.py"), "w") as f:
            f.write("raise RuntimeError('broken')\n")
        with self.assertRaises(subprocess.CalledProcessError):
            generate(project, seed=1)
        self.assertFalse(os.path.exists(os.path.join(project, "_output", "240801", "CCLF4")))


if __name__ == "__main__":
    unittest.main()
