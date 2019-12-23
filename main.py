import sys
if sys.version_info[0] < 3:
    raise SystemExit("Use Python 3 (or higher) only")

import base64
import re
import yaml

def isblank(string):
    return not(string) or string.isspace()

def decode_raw_value(raw_value, encoding):
    if isblank(raw_value): return raw_value

    if 'base64' == encoding:
        return base64.decodestring(raw_value)
    else:
        raise "encoding %s is not implemented!" % encoding

def replace_before_mapping(original_value, field_mapping):
    if not('replace' in field_mapping and original_value): return original_value

    replaces = field_mapping['replace']

    if isinstance(replaces, list):
        for reps in replaces:
            original_value = apply_replaces(original_value, reps)
    else:
        original_value = apply_replaces(original_value, replaces)

    return original_value

def apply_replaces(value, replaces):
    if isinstance(value, list):
        return map(lambda v: apply_replaces(v, replaces), value)
    else:
        for pattern, replacement in replaces.items():
            value = re.sub(pattern, replacement, value)

        return value

def mapped_value(original_value, field_mapping):
    return original_value

def apply_validations_on(field, value, validations):
    if validations['presence']: presence_validation_on(field, value)

def presence_validation_on(field, value):
    if isblank(value): raise "missing field: %s" % field

def mapped_line(line, line_mappings):
    rawtext = {}
    data    = {}

    for col, raw_value in enumerate(line):
        column_mapping = line_mappings[col]
        if column_mapping is None: raise 'Wrong number of columns'

        if column_mapping.get('do_not_capture'): continue

        # TODO: standard mapping

        rawtext_column_name = (column_mapping.get('rawtext_name') or column_mapping.get('column')).lower()

        for encoding in column_mapping.get('decode', []):
            raw_value = decode_raw_value(raw_value, encoding)

        rawtext[rawtext_column_name] = raw_value

        for field_mapping in column_mapping.get('mappings', []):
            original_value = raw_value

            original_value = replace_before_mapping(original_value, field_mapping)
            value = mapped_value(original_value, field_mapping)

            validations = field_mapping.get('validates')
            if validations: apply_validations_on(field_mapping['field'], value, validations)

            if isblank(value) and not(field_mapping.get('join')): continue

            field = field_mapping.get('field')

            data[field] = data.get(field, {})
            data[field]['values'] = data[field].get('values', [])
            if not('compact' in data[field]): data[field]['compact'] = True

            if field_mapping.get('order'):
                data[field]['join'] = data[field].get('join', field_mapping.get('join'))

                if 'compact' in field_mapping:
                    data[field]['compact'] = field_mapping['compact']

                data[field]['values'][field_mapping['order'] - 1] = value
            elif field_mapping.get('priority'):
                data[field]['values'][field_mapping['priority']] = value
            else:
                data[field]['values'].insert(0, value)

    attributes = {}

    for field, field_data in data.items():
        values = field_data['values']

        if 'join' in field_data:
            # Map "blank" values to None:
            values = map(lambda v: v or None, values)

            if field_data['compact']:
                values = list(filter(None, values))

            attributes[field] = field_data['join'].join(values)
        else:
            attributes[field] = next((v for v in field_data['values']), None)

    attributes['rawtext'] = rawtext # Assign last

    return attributes

mapping_yaml = """
- column: consultantcode
  mappings:
  - field: consultantcode
- column: hospital
  mappings:
  - field: hospital
    replace:
    - ? 'Addenbrookes'
      : 'RGT01'
"""

mapping = yaml.load(mapping_yaml, Loader=yaml.FullLoader)

lines = [
    ['bob', 'Addenbrookes Hospital'],
    ['gob', 'Peterborough Hospital']
]

for line in lines:
    print(mapped_line(line, mapping))
