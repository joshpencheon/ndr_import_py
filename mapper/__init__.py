"""
A Python port of ndr_import's mapper module.

Primarily defines:

    mapped_line(line, line_mappings)

Known issues:
* Doesn't support serialised Ruby Regexps - needs native pattern instead.
* Doesn't support legacy date formats (e.g. yyyy/mm/dd - needs %Y/%m/%d)
* Not all "clean" directives are supported.
"""

import base64
import copy
from datetime import datetime
import re
import sys
import yaml

if sys.version_info[0] < 3:
    raise SystemExit('Use Python 3 (or higher) only')

def isblank(obj):
    """
    port of Ruby's Object#blank?
    """
    return not(obj) or \
           (isinstance(obj, str) and obj.isspace()) or \
           (hasattr(obj, 'length') and obj.length == 0)

def clean(string, what):
    """
    port of ndr_support's string cleaning behaviour.
    Assumes a "symbol" for the value of `what`.
    """
    if what == ':sex':
        if re.match('^M|1', string, re.I):
            return '1'
        if re.match('^F|2', string, re.I):
            return '2'
        return '0'

    if what == ':name':
        substitutions = {
            '\.': '',
            ',|;': ' ',
            '\s{2,}': ' ',
            '`': '\''
        }

        string = string.upper()

        for pattern, replacement in substitutions.items():
            string = re.sub(pattern, replacement, string)

        return string.strip()

    if what == ':nhsnumber':
        return re.sub('[^0-9]', '', string)[0:10]

    if what == ':ethniccategory':
        return {
            '0': '0',
            '1': 'M',
            '2': 'N',
            '3': 'H',
            '4': 'J',
            '5': 'K',
            '6': 'R',
            '7': '8',
            '&': 'X',
            ' ': 'X',
            '99': 'X'
        }.get(string, string.upper())

    if what == ':upcase':
        return string.upper()

    if what == ':code':
        codes = []

        for code in re.split(' |,|;', string):
           code = re.sub('\.', '', code)

           if isblank(code):
               continue

           codes.append(code)

        return ' '.join(codes)

    raise Exception('unknown cleaner: %s!' % what)

def decode_raw_value(raw_value, encoding):
    """
    attempts to interpret `raw_value` from `encoding`
    """
    if isblank(raw_value):
        return raw_value

    if encoding == 'base64':
        return base64.b64decode(raw_value)

    raise Exception("encoding %s is not implemented!" % encoding)

def replace_before_mapping(original_value, field_mapping):
    """
    iterates over any replaces in the `field_mapping`, and
    applies them to any `original_value`(s).
    """
    if not('replace' in field_mapping and original_value):
        return original_value

    replaces = field_mapping['replace']

    if isinstance(replaces, list):
        for reps in replaces:
            original_value = apply_replaces(original_value, reps)
    else:
        original_value = apply_replaces(original_value, replaces)

    return original_value

def apply_replaces(value, replaces):
    """
    applies each replacement to the given value.
    """
    if isinstance(value, list):
        return list(map(lambda v: apply_replaces(v, replaces), value))

    for pattern, replacement in replaces.items():
        value = re.sub(pattern, replacement, value)

    return value

def mapped_value(original_value, field_mapping):
    """
    applies the first mapping to the given original_value.
    """
    if 'format' in field_mapping:
        if isblank(original_value):
            return None

        try:
            return datetime.strptime(original_value, field_mapping['format'])
        except ValueError:
            return None

    if 'clean' in field_mapping:
        cleaner = field_mapping['clean']
        if isinstance(cleaner, list):
            for cln in cleaner:
                original_value = clean(original_value, cln)
        else:
            original_value = clean(original_value, cleaner)
        return original_value

    if 'map' in field_mapping:
        return field_mapping['map'].get(original_value, original_value)

    if 'match' in field_mapping:
        match = re.search(field_mapping['match'], original_value)
        return match and match.group(1)

    if 'daysafter' in field_mapping:
        # TODO: implement daysafter
        raise Exception('daysafter is not implemented!')

    if isblank(original_value):
        return None

    if isinstance(original_value, str):
        return original_value.strip()

    return original_value

def apply_validations_on(field, value, validations):
    """
    raises if any of the requested validations do not
    pass against the given field's value.
    """
    if validations['presence']:
        presence_validation_on(field, value)

def presence_validation_on(field, value):
    """
    raises if the supplied value is blank.
    """
    if isblank(value):
        raise Exception("%s can't be blank" % field)

def validate_line_mappings(line_mappings):
    """
    raises if the supplied mappings are non-sensical:
        * checks all standard mappings exist
        * checks all priorities are unique within a field
    """
    priorities = {}

    for column_mapping in line_mappings:
        if column_mapping.get('standard_mapping'):
            name = column_mapping['standard_mapping']

            if not standard_mapping(name, column_mapping):
                raise Exception("Standard mapping '%s' does not exist!" % name)

        if 'mappings' not in column_mapping:
            continue
        
        for field_mapping in column_mapping['mappings']:
            field = field_mapping['field']
            priority = field_mapping.get('priority')

            if priority:
                if priorities.get(field) == priority:
                    raise Exception("Field '%s' cannot have duplicate priorities!" % field)

                priorities[field] = priority
            else:
                priorities[field] = 1

def mapped_line(line, line_mappings):
    """
    applies mapping to the given line.
    """
    validate_line_mappings(line_mappings)

    rawtext = {}
    data = {}

    for col, raw_value in enumerate(line):
        column_mapping = line_mappings[col]
        if not column_mapping:
            raise Exception('Wrong number of columns')

        if column_mapping.get('do_not_capture'):
            continue

        if 'standard_mapping' in column_mapping:
            column_mapping = standard_mapping(column_mapping['standard_mapping'], column_mapping)

        rawtext_column_name = (column_mapping.get('rawtext_name') or
                               column_mapping['column']).lower()

        for encoding in column_mapping.get('decode', []):
            raw_value = decode_raw_value(raw_value, encoding)

        rawtext[rawtext_column_name] = raw_value

        for field_mapping in column_mapping.get('mappings', []):
            original_value = raw_value

            original_value = replace_before_mapping(original_value, field_mapping)
            value = mapped_value(original_value, field_mapping)
            validations = field_mapping.get('validates')
            if validations:
                apply_validations_on(field_mapping['field'], value, validations)

            if isblank(value) and not field_mapping.get('join'):
                continue

            field = field_mapping.get('field')

            data[field] = data.get(field, {})
            data[field]['values'] = data[field].get('values', {})
            if 'compact' not in data[field]:
                data[field]['compact'] = True

            if field_mapping.get('order'):
                data[field]['join'] = data[field].get('join', field_mapping.get('join'))

                if 'compact' in field_mapping:
                    data[field]['compact'] = field_mapping['compact']

                data[field]['values'][field_mapping['order'] - 1] = value
            elif field_mapping.get('priority'):
                data[field]['values'][field_mapping['priority']] = value
            else:
                data[field]['values'][0] = value

    attributes = {}

    for field, field_data in data.items():
        # Stored in a dict by "index", retrieve sorted actual values:
        value_dict = field_data['values']
        values = list(map(lambda k: value_dict[k], sorted(value_dict)))

        if 'join' in field_data:
            # Map "blank" values to None:
            values = map(lambda v: v or None, values)

            if field_data['compact']:
                values = list(filter(None, values))

            attributes[field] = field_data['join'].join(map(lambda v: v or '', values))
        else:
            attributes[field] = next((v for v in values), None)

    attributes['rawtext'] = rawtext # Assign last

    return attributes

STANDARD_MAPPINGS_YAML = """
surname:
  column: surname
  rawtext_name: surname
  mappings:
  - field: surname
    clean: :name
previoussurname:
  column: previoussurname
  rawtext_name: previoussurname
  mappings:
  - field: previoussurname
    clean: :name
forenames:
  column: forenames
  rawtext_name: forenames
  mappings:
  - field: forenames
    clean: :name
sex:
  column: sex
  rawtext_name: sex
  mappings:
  - field: sex
    clean: :sex
nhsnumber:
  column: nhsnumber
  rawtext_name: nhsnumber
  mappings:
  - field: nhsnumber
    clean: :nhsnumber
postcode:
  column: postcode
  rawtext_name: postcode
  mappings:
  - field: postcode
    clean: :postcode
test:
  column: standard_mapping_column_name
"""

STANDARD_MAPPINGS = yaml.load(STANDARD_MAPPINGS_YAML, Loader=yaml.FullLoader)

def standard_mapping(mapping_name, column_mapping):
    """
    Looks for a standard mapping matching the given name,
    and merges it into the supplied column mapping.
    """
    mapping = STANDARD_MAPPINGS.get(mapping_name)
    if not mapping:
        return None

    result = copy.copy(mapping)

    for key, value in column_mapping.items():
        # "mappings" append, everything else replaces:
        if key == 'mappings':
            result[key] = result.get(key, []) + value
        else:
            result[key] = value

    return result

if __name__ == "__main__":
    MAPPING_YAML = """
    - standard_mapping: forenames
    - column: hospital
      mappings:
      - field: hospital
        replace:
        - ? 'Addenbrookes'
          : 'RGT01'
    """

    MAPPING = yaml.load(MAPPING_YAML, Loader=yaml.FullLoader)

    LINES = [
        [' bob ', 'Addenbrookes Hospital'],
        ['gob', 'Peterborough Hospital']
    ]

    for l in LINES:
        print(mapped_line(l, MAPPING))
