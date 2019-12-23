# NdrImport Mapper (Python Port)

This is an experimental port of the mapper logic found in the `ndr_import` Ruby gem.

## Setup

Install required packages using `pip`:

```bash
pip install -r requirements.txt
```

## Usage

```python
from mapper import mapped_line

mapped_line(['A', 'B', 'C'], mapping)
```

### Known issues
* Doesn't support serialised Ruby Regexps - needs native pattern instead.
* Doesn't support legacy date formats (e.g. yyyy/mm/dd - needs %Y/%m/%d)
* Not all "clean" directives are supported.

## Run the tests

```bash
python test_mapper.py
```
