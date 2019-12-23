from datetime import datetime
import unittest
import textwrap
import yaml

from mapper import mapped_line, mapped_value, replace_before_mapping

def yaml_load(string):
    return yaml.load(textwrap.dedent(string), Loader=yaml.FullLoader)

# TODO: support dd/mm/yyyy / yyyymmdd
format_mapping = { 'format': '%d/%m/%Y' }
format_mapping_yyyymmdd = { 'format': '%Y%m%d' }
clean_name_mapping = { 'clean': ':name' }
clean_ethniccategory_mapping = { 'clean': ':ethniccategory' }
clean_icd_mapping = { 'clean': ':icd' }
clean_opcs_mapping = { 'clean': ':code_opcs' }
clean_code_and_upcase_mapping = { 'clean': [':code', ':upcase'] }
map_mapping = { 'map': { 'A': '1' } }
replace_mapping = { 'replace': { '.0': '' } }
daysafter_mapping = { 'daysafter': '2012-05-16' }
# TODO: match_mapping = {}

simple_mapping = [{ 'column': 'patient address', 'mappings': [{ 'field': 'address' }] } ]

simple_mapping_with_clean_opcs = yaml_load("""\
- column: primaryprocedures
  mappings:
  - field: primaryprocedures
    clean: :code_opcs
""")

join_mapping = yaml_load("""\
- column: forename1
  mappings:
  - field: forenames
    order: 1
    join: " "
- column: forename2
  mappings:
  - field: forenames
    order: 2
""")

join_compact_mapping = yaml_load("""\
- column: forename1
  mappings:
  - field: forenames
    order: 1
    join: " "
    compact: false
- column: forename2
  mappings:
  - field: forenames
    order: 2
""")

cross_populate_mapping = yaml_load("""\
- column: referringclinicianname
  mappings:
  - field: consultantname
  - field: consultantcode
    priority: 2
- column: referringcliniciancode
  mappings:
  - field: consultantcode
""")

cross_populate_replace_mapping = yaml_load("""\
- column: referringclinicianname
  mappings:
  - field: consultantname
  - field: consultantcode
    priority: 2
    replace:
      ? ^BOB FOSSIL$
      : "ROBERT FOSSIL"
- column: referringcliniciancode
  mappings:
  - field: consultantcode
    priority: 1
""")

cross_populate_map_mapping = yaml_load("""\
- column: referringclinicianname
  mappings:
  - field: consultantname
  - field: consultantcode
    priority: 2
    map:
      "Bob Fossil": "C5678"
- column: referringcliniciancode
  mappings:
  - field: consultantcode
    priority: 1
""")

cross_populate_map_reverse_priority_mapping = yaml_load("""\
- column: referringclinicianname
  mappings:
  - field: consultantname
  - field: consultantcode
    priority: 1
    map:
      "Bob Fossil": "C5678"
      "Bolo": ""
- column: referringcliniciancode
  mappings:
  - field: consultantcode
    priority: 2
""")

cross_populate_order_mapping = yaml_load("""\
- column: referringclinicianname
  mappings:
  - field: consultantname
  - field: consultantcode
    priority: 2
- column: referringcliniciancode
  mappings:
  - field: consultantcode
    priority: 1
- column: somecolumn
  mappings:
  - field: consultantcode
    priority: 5
- column: anothercolumn
  mappings:
  - field: consultantcode
    priority: 10
""")

cross_populate_no_priority = yaml_load("""\
- column: columnoneraw
  mappings:
  - field: columnone
  - field: columntwo
- column: columntworaw
  mappings:
  - field: columntwo
    priority: 5
""")

standard_mapping_without = yaml_load("""\
- column: surname
  rawtext_name: surname
  mappings:
  - field: surname
    clean: :name
- column: forename
  rawtext_name: forenames
  mappings:
  - field: forenames
    clean: :name
- column: sex
  rawtext_name: sex
  mappings:
  - field: sex
    clean: :sex
- column: nhs_no
  rawtext_name: nhsnumber
  mappings:
  - field: nhsnumber
    clean: :nhsnumber
""")

standard_mapping_with = yaml_load("""\
- standard_mapping: surname
- column: forename
  standard_mapping: forenames
- standard_mapping: sex
- column: nhs_no
  standard_mapping: nhsnumber
""")

standard_mapping_merge = yaml_load("""\
- column: surname
  standard_mapping: surname
  mappings:
  - field: surname2
""")

standard_mapping_column = yaml_load("""\
- column: overriding_column_name
  standard_mapping: test
""")

invalid_priorities = yaml_load("""\
- column: columnoneraw
  mappings:
  - field: columnone
  - field: columntwo
    priority: 5
- column: columntworaw
  mappings:
  - field: columntwo
    priority: 5
""")

invalid_standard_mapping = yaml_load("""\
- column: surname
  standard_mapping: surnames
""")

joined_mapping_blank_start = yaml_load("""\
- column: addressoneraw
  mappings:
  - field: address
    join: ","
    order: 1
- column: postcode
  mappings:
  - field: address
    order: 2
""")

joined_mapping_blank_start_uncompacted = yaml_load("""\
- column: addressoneraw
  mappings:
  - field: address
    join: ","
    order: 1
    compact: false
- column: postcode
  mappings:
  - field: address
    order: 2
""")

date_mapping = yaml_load("""\
- column: birth_date
  rawtext_name: dateofbirth
  mappings:
  - field: dateofbirth
    format: dd/mm/yyyy
- column: received_date
  rawtext_name: receiveddate
  mappings:
  - field: receiveddate
    format: yyyymmdd
- column: american_date
  rawtext_name: americandate
  mappings:
  - field: americandate
    format: mm/dd/yyyy
- column: short_date
  rawtext_name: shortdate
  mappings:
  - field: shortdate
    format: dd/mm/yy
- column: funky_date
  rawtext_name: funkydate
  mappings:
  - field: funkydate
    format: dd/mmm/yy
""")

do_not_capture_column = yaml_load("""\
- column: ignore_me
  do_not_capture: true
""")

base64_mapping = yaml_load("""\
- column: base64
  decode:
  - :base64
  - :word_doc
""")

invalid_decode_mapping = yaml_load("""\
- column: column_name
  decode:
  - :invalid_encoding
""")

replace_array_mapping = yaml_load("""\
- column: consultantcode
  mappings:
  - field: consultantcode
- column: hospital
  mappings:
  - field: hospital
    replace:
    - ? Addenbrookes
      : 'RGT01'
""")

validates_presence_mapping = yaml_load("""\
- column: column_one
  mappings:
  - field: field_one
    validates:
      presence: true
- column: column_two
  mappings:
  - field: field_two
""")

class TestMapper(unittest.TestCase):

    def test_map_should_return_a_number(self):
        self.assertEqual('1', mapped_value('A', map_mapping))

    def test_map_should_return_unmapped(self):
        self.assertEqual('B', mapped_value('B', map_mapping))

    def test_map_should_return_correct_date_format(self):
        self.assertEqual(datetime(2011, 1, 25), mapped_value('25/01/2011', format_mapping))
        self.assertEqual(datetime(2011, 1, 25), mapped_value('20110125', format_mapping_yyyymmdd))

    def test_map_should_return_incorrect_date_format(self):
        self.assertNotEqual(datetime(2011, 3, 4), mapped_value('03/04/2011', format_mapping))

    def test_map_should_return_no_date_format(self):
        self.assertIsNone(mapped_value('03/25/2011', format_mapping))

    def test_map_should_replace_value(self):
        self.assertEqual('2', replace_before_mapping('2.0', replace_mapping))

    def test_map_should_not_alter_value(self):
        self.assertEqual('2.1', replace_before_mapping('2.1', replace_mapping))

    @unittest.skip('not implemented yet')
    def test_map_should_clean_name(self):
        self.assertEqual('ANNABELLE SMITH', mapped_value('anna.belle,smith', clean_name_mapping))

    @unittest.skip('not implemented yet')
    def test_map_should_clean_ethnic_category(self):
        self.assertEqual('M', mapped_value('1', clean_ethniccategory_mapping))
        self.assertEqual('X', mapped_value('99', clean_ethniccategory_mapping))
        self.assertEqual('A', mapped_value('A', clean_ethniccategory_mapping))
        self.assertEqual('INVALID', mapped_value('InVaLiD', clean_ethniccategory_mapping))

    @unittest.skip('not implemented yet')
    def test_map_should_clean_icd_code(self):
        self.assertEqual('C343 R932 Z515', mapped_value('C34.3,R93.2,Z51.5', clean_icd_mapping))

    @unittest.skip('not implemented yet')
    def test_map_should_clean_opcs_code(self):
        self.assertEqual('U212 Y973', mapped_value('U212,Y973,X1', clean_opcs_mapping))
        self.assertEqual('', mapped_value('98', clean_opcs_mapping))
        self.assertEqual('', mapped_value('TooLong', clean_opcs_mapping))
        self.assertIsNone('', mapped_value('', clean_opcs_mapping))
        self.assertEqual('ABCD', mapped_value('AbcD', clean_opcs_mapping))
        self.assertEqual('1234', mapped_value('1234', clean_opcs_mapping))

    @unittest.skip('not implemented yet')
    def test_map_should_use_multiple_cleans(self):
        self.assertEqual('U3 Y2 X1', mapped_value('u3,y2,x1', clean_code_and_upcase_mapping))

if __name__ == '__main__':
    unittest.main()
