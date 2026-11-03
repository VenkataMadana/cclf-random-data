# CCLF File Layouts

This set of scripts generates fake files and data to adhere to the
specifications outlined in the CMS Accountable Care Organization – Operational
System (ACO-OS) Claim and Claim Line Feed (CCLF) Information Packet (IP) Version
38.0, dated 02/02/2024

The PDF for this specification can be
[downloaded here](https://www.cms.gov/files/document/cclf-information-packet.pdf).

Each of the file types is generated using a Python script that generates random
data based on the specifications provided in the PDF.

## Setup

Install the pinned dependency. The project is tested on Python 3.14.

```bash
python3 -m pip install -r requirements.txt
```

## Generating files

Execute `main.py` from the root of the repository to generate the files:

```bash
python3 main.py
```

This will generate fake CCLF files for each of the file types listed in the PDF.
Any contents of the `_output` directory from earlier runs are deleted first.

The defaults for the population sizes and the claims month are at the top of
`main.py`. The sizes can also be set when running the script:

```bash
python3 main.py --beneficiaries 100 --providers 200 --claims 1000
```

Each run prints its seed. Pass it back with `--seed` to generate the same files
again using the same version of Faker:

```bash
python3 main.py --seed 12345
```

The generated files will be written to the `_output` directory and have a
filename that includes the date, time, and type of file. The filenames follow
the formats specified in the requirements.

Each claim belongs to one family and is only written to that family's files:

| Family | Claim types | Files |
| --- | --- | --- |
| Part A | 10, 20, 30, 40, 50, 60, 61 | CCLF1, CCLF2, CCLF3, CCLF4, CCLFA |
| Part B | 71, 72 | CCLF5, CCLFB |
| DME | 81, 82 | CCLF6 |
| Part D | 01, 02, 03 | CCLF7 |

Each file contains random data based on the specifications provided in the PDF.

The scripts use [Faker](https://faker.readthedocs.io/en/master/) to produce
pseudo-random data for fields such as dates and names. The Faker library is used
to generate realistic looking data, but it does not guarantee that the data will
be realistic or accurate in any way.

## Tests

The tests generate files in a temporary directory and check them against the
field layouts in the PDF. They do not touch the `_output` directory.

```bash
python3 -m unittest discover tests
```

## Resources

- [Beneficiary Dual Status Code](https://resdac.org/cms-data/variables/edual1-12)
- [Carrier Claim Payment Denial Code](https://resdac.org/cms-data/variables/carrier-claim-payment-denial-code)
- [Claim Diagnosis Code I Diagnosis Present on Admission (POA) Indicator Code (FFS)](https://resdac.org/cms-data/variables/claim-diagnosis-code-i-diagnosis-present-admission-poa-indicator-code-ffs)
- [Claim Frequency Code (FFS)](https://resdac.org/cms-data/variables/claim-frequency-code-ffs)
- [Claim Medicare Non-Payment Reason Code](https://resdac.org/cms-data/variables/claim-medicare-non-payment-reason-code)
- [Claim Service Classification Type Code Table](https://resdac.org/cms-data/variables/claim-service-classification-type-code-ffs)
- [Claim Source Inpatient Admission Code (FFS)](https://resdac.org/cms-data/variables/claim-source-inpatient-admission-code-ffs)
- [Line CMS Provider Specialty Code](https://resdac.org/cms-data/variables/line-cms-provider-specialty-code)
- [Line CMS Type Service Code](https://resdac.org/cms-data/variables/line-cms-type-service-code)
- [Line Place Of Service Code (FFS)](https://resdac.org/cms-data/variables/line-place-service-code-ffs)
- [Line Primary Payer Code (if not Medicare)](https://resdac.org/cms-data/variables/line-primary-payer-code-if-not-medicare)
- [Line Processing Indicator Code](https://resdac.org/cms-data/variables/line-processing-indicator-code)
- [NCH Primary Payer Code (if not Medicare)](https://resdac.org/cms-data/variables/nch-primary-payer-code-if-not-medicare)
- [Patient Discharge Status Code (FFS)](https://resdac.org/cms-data/variables/patient-discharge-status-code-ffs)
- [Revenue Center APC or HIPPS Code](https://resdac.org/cms-data/variables/revenue-center-apc-or-hipps-code)
- [Revenue Center Code (FFS)](https://resdac.org/cms-data/variables/revenue-center-code-ffs)
- [FIPS State and County Codes](https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt)

