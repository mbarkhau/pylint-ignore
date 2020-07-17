# Catalog file for `pylint-ignore`

This file is parsed by `pylint-ignore` to determine which `pylint` messages are ignored.

The reccomended approach to using `pylint-ignore` is:

- If a message is valid, update your code rather than ignoring the message.
- If a message should always be ignored, to do so via the usual
  `pylintrc` file or `setup.cfg` file rather than this `pylint-ignore.md`
  file.
- If a message should be ignored, write a short comment why it is ok.
- If a message should not be ignored, remove the section.


## File: src/pylint_ignore/__main__.py

### Line 96 - R0902 (too-many-instance-attributes)

- message: Too many instance attributes (10/7)
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T09:59:24
- ignored: yes

```
  94:
  95:
> 96: class PylintIgnoreDecorator:
  97:     # NOTE (mb 2020-07-17): The term "Decorator" refers to the gang of four
  98:     #   pattern, rather than the typical usage in python which is about function
```


### Line 160 - W0511 (fixme)

- message: TODO (mb 2020-07-17): This will override any configuration, but it is not
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T11:39:54


```
  129:     def _parse_args(self, args: typ.Sequence[str]) -> None:
  ...
  158:             arg_i += 1
  159:
> 160:         # TODO (mb 2020-07-17): This will override any configuration, but it is not
  161:         #   ideal. It would be better if we could use the same config parsing logic
  162:         #   as pylint and raise an error if anything other than jobs=1 is configured
```


### Line 280 - W0102 (dangerous-default-value)

- message: Dangerous default value sys.argv[1:] (builtins.list) as argument
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T21:15:25
- ignored: this is safe, we don't mutate args

```
  278:
  279:
> 280: def main(args: typ.Sequence[str] = sys.argv[1:]) -> ExitCode:
  281:     dec = PylintIgnoreDecorator(args)
  282:     try:
```


## File: src/pylint_ignore/catalog.py

### Line 242 - E1101 (no-member)

- message: Instance of 'SourceText' has no '_replace' member
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T23:53:07
- ignored: yes, too bad pylint doesn't know about NamedTuple

```
  224: def _init_entry_item(entry_vals: EntryValues) -> typ.Tuple[Key, Entry]:
  ...
  240:
  241:     # preserve old lineno, otherwise the catalog won't be updated
> 242:     srctxt = srctxt._replace(lineno=old_lineno)
  243:
  244:     catalog_entry = Entry(
```


