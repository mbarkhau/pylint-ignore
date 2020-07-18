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

### Line 110 - R0902 (too-many-instance-attributes)

- message: Too many instance attributes (10/7)
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T09:59:24
- path   : src/pylint_ignore/__main__.py
- ignored: yes

```
  108:
  109:
> 110: class PylintIgnoreDecorator:
  111:     # NOTE (mb 2020-07-17): The term "Decorator" refers to the gang of four
  112:     #   pattern, rather than the typical usage in python which is about function
```


### Line 174 - W0511 (fixme)

- message: TODO (mb 2020-07-17): This will override any configuration, but it is not
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T11:39:54
- path   : src/pylint_ignore/__main__.py


```
  143:     def _parse_args(self, args: typ.Sequence[str]) -> None:
  ...
  172:             arg_i += 1
  173:
> 174:         # TODO (mb 2020-07-17): This will override any configuration, but it is not
  175:         #   ideal. It would be better if we could use the same config parsing logic
  176:         #   as pylint and raise an error if anything other than jobs=1 is configured
```


### Line 297 - W0102 (dangerous-default-value)

- message: Dangerous default value sys.argv[1:] (builtins.list) as argument
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T21:15:25
- path   : src/pylint_ignore/__main__.py
- ignored: this is safe, we don't mutate args, mypy would catch it if we do

```
  295:
  296:
> 297: def main(args: typ.Sequence[str] = sys.argv[1:]) -> ExitCode:
  298:     dec = PylintIgnoreDecorator(args)
  299:     try:
```


