import copy
from datetime import datetime
import unittest
import textwrap
import yaml

from mapper import mapped_line, mapped_value, replace_before_mapping, STANDARD_MAPPINGS

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

unused_mapping = [{ 'column': 'extra', 'rawtext_name': 'extra' }]

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
      ? (?i)^BOB FOSSIL$
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

    def test_map_should_handle_array_original_value(self):
        original_value = ['C9999998', ['Addenbrookes', 'RGT01']]
        mapped_value = mapped_line(original_value, replace_array_mapping)
        self.assertEqual(['RGT01', 'RGT01'], mapped_value['hospital'])

    def test_should_raise_error_on_missing_mandatory_field(self):
        with self.assertRaises(Exception) as cm:
            mapped_line(['', 'RGT01'], validates_presence_mapping)

        self.assertEqual("field_one can't be blank", str(cm.exception))

    @unittest.skip('not implemented yet')
    def test_should_return_correct_date_format_for_date_fields_with_daysafter(self):
        self.assertEqual(datetime(2012, 5, 18), mapped_value(2, daysafter_mapping))
        self.assertEqual(datetime(2012, 5, 18), mapped_value('2', daysafter_mapping))
        self.assertEqual(datetime(2012, 5, 14), mapped_value(-2, daysafter_mapping))
        self.assertEqual(datetime(2012, 5, 14), mapped_value('-2', daysafter_mapping))
        self.assertEqual(datetime(2012, 5, 16), mapped_value(0, daysafter_mapping))
        self.assertEqual('String', mapped_value('String', daysafter_mapping))
        self.assertEqual('', mapped_value('', daysafter_mapping))
        self.assertIsNone(mapped_value(None, daysafter_mapping))
        self.assertEqual(datetime(2057, 8, 23), mapped_value(16535, daysafter_mapping))
        # Answer independently checked http://www.wolframalpha.com/input/?i=2012-05-16+%2B+9379+days
        self.assertEqual(datetime(2038, 1, 19), mapped_value(9379, daysafter_mapping))
        self.assertEqual(datetime(1946, 5, 11), mapped_value(16900, {'daysafter': '1900-02-01'}))
        self.assertEqual(datetime(2014, 4, 8), mapped_value(16900, {'daysafter': '1967-12-31'}))
        self.assertEqual(datetime(2046, 4, 9), mapped_value(16900, {'daysafter': '2000-01-01'}))

    def test_line_mapping_should_create_valid_hash(self):
        line_hash = mapped_line(['1 test road, testtown'], simple_mapping)
        self.assertEqual('1 test road, testtown', line_hash['address'])
        self.assertEqual('1 test road, testtown', line_hash['rawtext']['patient address'])

    @unittest.skip('not implemented yet')
    def test_line_mapping_should_create_valid_hash_with_blank_cleaned_value(self):
        self.assertEqual('', mapped_value('98', clean_opcs_mapping))
        line_hash = mapped_line(['98'], simple_mapping_with_clean_opcs)
        self.assertIsNone(line_hash['primaryprocedures'])
        self.assertEqual('98', line_hash['rawtext']['primaryprocedures'])

    def test_line_mapping_should_create_valid_hash_with_join(self):
        line_hash = mapped_line(['Catherine', 'Elizabeth'], join_mapping)
        self.assertEqual('Catherine Elizabeth', line_hash['forenames'])
        self.assertEqual('Catherine', line_hash['rawtext']['forename1'])
        self.assertEqual('Elizabeth', line_hash['rawtext']['forename2'])

    def test_line_mapping_should_create_valid_hash_with_rawtext_only(self):
        line_hash = mapped_line(['otherinfo'], unused_mapping)
        self.assertEqual(1, len(line_hash))
        self.assertEqual('otherinfo', line_hash['rawtext']['extra'])

    def test_should_create_valid_hash_with_unused_cross_populate(self):
        line_hash = mapped_line(['Bob Fossil', 'C1234'], cross_populate_mapping)
        self.assertEqual('Bob Fossil', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('C1234', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('Bob Fossil', line_hash['consultantname'])
        self.assertEqual('C1234', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_used_cross_populate(self):
        line_hash = mapped_line(['Bob Fossil', ''], cross_populate_mapping)
        self.assertEqual('Bob Fossil', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('Bob Fossil', line_hash['consultantname'])
        self.assertEqual('Bob Fossil', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_unused_cross_populate_replace(self):
        line_hash = mapped_line(['Bob Fossil', 'C1234'], cross_populate_replace_mapping)
        self.assertEqual('Bob Fossil', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('C1234', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('Bob Fossil', line_hash['consultantname'])
        self.assertEqual('C1234', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_used_cross_populate_replace(self):
        line_hash = mapped_line(['Bob Fossil', ''], cross_populate_replace_mapping)
        self.assertEqual('Bob Fossil', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('Bob Fossil', line_hash['consultantname'])
        self.assertEqual('ROBERT FOSSIL', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_used_cross_populate_without_replace(self):
        line_hash = mapped_line(['Bob Smith', ''], cross_populate_replace_mapping)
        self.assertEqual('Bob Smith', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('Bob Smith', line_hash['consultantname'])
        self.assertEqual('Bob Smith', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_unused_cross_populate_map(self):
        line_hash = mapped_line(['Bob Fossil', 'C1234'], cross_populate_map_mapping)
        self.assertEqual('Bob Fossil', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('C1234', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('Bob Fossil', line_hash['consultantname'])
        self.assertEqual('C1234', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_used_cross_populate_with_map(self):
        line_hash = mapped_line(['Bob Fossil', ''], cross_populate_map_mapping)
        self.assertEqual('Bob Fossil', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('Bob Fossil', line_hash['consultantname'])
        self.assertEqual('C5678', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_used_cross_populate_with_map_with_no_p2_map(self):
        line_hash = mapped_line(['something', ''], cross_populate_map_mapping)
        self.assertEqual('something', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('something', line_hash['consultantname'])
        self.assertEqual('something', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_used_cross_populate_with_map_with_p1_mapped(self):
        line_hash = mapped_line(['Bob Fossil', 'P2'], cross_populate_map_reverse_priority_mapping)
        self.assertEqual('Bob Fossil', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('P2', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('Bob Fossil', line_hash['consultantname'])
        self.assertEqual('C5678', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_used_cross_populate_with_map_with_p1_mapped_out(self):
        line_hash = mapped_line(['Bolo', 'P2'], cross_populate_map_reverse_priority_mapping)
        self.assertEqual('Bolo', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('P2', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('Bolo', line_hash['consultantname'])
        self.assertEqual('P2', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_used_cross_populate_with_map_with_p1_no_map(self):
        line_hash = mapped_line(['something', 'P2'], cross_populate_map_reverse_priority_mapping)
        self.assertEqual('something', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('P2', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('something', line_hash['consultantname'])
        self.assertEqual('something', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_used_cross_populate_without_map(self):
        line_hash = mapped_line(['Bob Smith', ''], cross_populate_map_mapping)
        self.assertEqual('Bob Smith', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('Bob Smith', line_hash['consultantname'])
        self.assertEqual('Bob Smith', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_used_cross_populate_without_map_and_priorities(self):
        line_hash = mapped_line(['Pass', '', 'Fail', 'Large Fail'], cross_populate_order_mapping)
        self.assertEqual('Pass', line_hash['rawtext']['referringclinicianname'])
        self.assertEqual('', line_hash['rawtext']['referringcliniciancode'])
        self.assertEqual('Pass', line_hash['consultantname'])
        self.assertEqual('Pass', line_hash['consultantcode'])

    def test_should_create_valid_hash_with_used_cross_populate_without_priority(self):
        line_hash = mapped_line(['Exists', 'Not'], cross_populate_no_priority)
        self.assertEqual('Exists', line_hash['rawtext']['columnoneraw'])
        self.assertEqual('Not', line_hash['rawtext']['columntworaw'])
        self.assertEqual('Exists', line_hash['columnone'])
        self.assertEqual('Exists', line_hash['columntwo'])

    @unittest.skip('not implemented yet')
    def test_should_create_equal_hashes_with_standard_mapping(self):
        line_hash_without = mapped_line(
          ['Smith', 'John F', 'male', '01234567'], standard_mapping_without
        )
        line_hash_with = mapped_line(
          ['Smith', 'John F', 'male', '01234567'], standard_mapping_with
        )
        self.assertEqual(line_hash_without, line_hash_with)

    @unittest.skip('not implemented yet')
    def test_should_merge_standard_mapping_and_normal_mapping(self):
        line_hash = mapped_line(['Smith'], standard_mapping_merge)
        self.assertEqual('SMITH', line_hash['surname'])
        self.assertEqual('Smith', line_hash['surname2'])

    @unittest.skip('not implemented yet')
    def test_should_merge_standard_mapping_in_correct_order(self):
        line_hash = mapped_line(['Smith'], standard_mapping_column)
        self.assertEqual('Smith', line_hash['rawtext']['overriding_column_name'])
        self.assertNotIn('standard_mapping_column_name', line_hash['rawtext'])

    @unittest.skip('validate_line_mappings not implemented yet')
    def test_should_raise_on_duplicate_priority(self):
        with self.assertRaises(Exception):
            mapped_line(['A', 'B'], invalid_priorities)

    @unittest.skip('validate_line_mappings not implemented yet')
    def test_should_raise_on_duplicate_priority(self):
        with self.assertRaises(Exception):
            mapped_line(['A'], invalid_standard_mapping)

    def test_should_not_modify_the_standard_mapping_when_using_it(self):
        standard_mappings = copy.deepcopy(STANDARD_MAPPINGS)

        mapping = [{
            'column': 'surname',
            'standard_mapping': 'surname',
            'mappings': [{'field': 'overwrite_surname'}]
        }]

        mapped_line(['Smith'], mapping)

        self.assertEqual(standard_mappings, STANDARD_MAPPINGS)

    def test_should_join_blank_first_field_with_compacting(self):
        line_hash = mapped_line(['', 'CB3 0DS'], joined_mapping_blank_start)
        self.assertEqual('CB3 0DS', line_hash['address'])

    def test_should_join_blank_first_field_without_compacting(self):
        line_hash = mapped_line(['', 'CB3 0DS'], joined_mapping_blank_start_uncompacted)
        self.assertEqual(',CB3 0DS', line_hash['address'])

    @unittest.skip('legacy date formats using mm/dd etc rather than %m/%d are not supported')
    def test_line_mapping_should_map_date_formats_correctly(self):
        real_date = datetime(1927, 7, 6)
        incomings = ['06/07/1927',  '19270706',     '07/06/1927',   '06/07/27',  '06/JUL/27']
        columns   = ['dateofbirth', 'receiveddate', 'americandate', 'shortdate', 'funkydate']
        line_hash = mapped_line(incomings, date_mapping)

        print(line_hash)
        for column_name in columns:
          self.assertEqual(real_date, line_hash[column_name])

    def test_should_ignore_columns_marked_do_not_capture(self):
        line_hash = mapped_line(['rubbish'], do_not_capture_column)
        self.assertNotIn('ignore_me', line_hash['rawtext'])


    @unittest.skip('MS Word decoding has not been implemented')
    def test_should_decode_base64_encoded_word_document(self):
        pass

    @unittest.skip('MS Word decoding has not been implemented')
    def test_should_decode_base64_encoded_docx_document(self):
        pass

    def test_should_raise_unknown_encoding_exception(self):
        with self.assertRaises(Exception):
            mapped_line(['A'], invalid_decode_mapping)

if __name__ == '__main__':
    unittest.main()
