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

### Line 94 - R0902 (too-many-instance-attributes)

- message: Too many instance attributes (10/7)
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T09:59:24
- ignored: yes

```
  92:
  93:
> 94: class PylintIgnoreDecorator:
  95:     # NOTE (mb 2020-07-17): The term "Decorator" refers to the gang of four
  96:     #   pattern, rather than the typical usage in python which is about function
```


### Line 158 - W0511 (fixme)

- message: TODO (mb 2020-07-17): This will override any configuration, but it is not
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T11:39:54


```
  127:     def _parse_args(self, args: typ.Sequence[str]) -> None:
  ...
  156:             arg_i += 1
  157:
> 158:         # TODO (mb 2020-07-17): This will override any configuration, but it is not
  159:         #   ideal. It would be better if we could use the same config parsing logic
  160:         #   as pylint and raise an error if anything other than jobs=1 is configured
```


### Line 199 - W0613 (unused-argument)

- message: Unused argument 'lineno'
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T09:59:24
- ignored: This is part of the pylint api.

```
  193:     def is_enabled_entry(
  ...
  197:         symbol  : str,
  198:         msg_text: str,
> 199:         lineno  : int,
  200:         srctxt  : catalog.MaybeSourceText,
  201:     ) -> bool:
```


### Line 280 - C0415 (import-outside-toplevel)

- message: Import outside toplevel (pylint.message.message_handler_mix_in.MessagesHandlerMixIn)
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T10:50:36
- ignored: because monkey patching

```
  276:     def monkey_patch_pylint(self) -> None:
  ...
  278:         #   found. Though I'm not quite sure why msg_descr that is a code would
  279:         #   imply that it's a candidate to generate output and otherwise not.
> 280:         from pylint.message.message_handler_mix_in import MessagesHandlerMixIn
  281:
  282:         self.pylint_is_message_enabled = MessagesHandlerMixIn.is_message_enabled
```


### Line 289 - C0415 (import-outside-toplevel)

- message: Import outside toplevel (pylint.message.message_handler_mix_in.MessagesHandlerMixIn)
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T21:15:25
- ignored: because monkey patching

```
  287:
  288:     def monkey_unpatch_pylint(self) -> None:
> 289:         from pylint.message.message_handler_mix_in import MessagesHandlerMixIn
  290:
  291:         MessagesHandlerMixIn.is_message_enabled = self.pylint_is_message_enabled
```


### Line 295 - W0102 (dangerous-default-value)

- message: Dangerous default value sys.argv[1:] (builtins.list) as argument
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T21:15:25
- ignored: this is safe, we don't mutate args

```
  293:
  294:
> 295: def main(args: typ.Sequence[str] = sys.argv[1:]) -> ExitCode:
  296:     dec = PylintIgnoreDecorator(args)
  297:     try:
```


### Line 303 - C0415 (import-outside-toplevel)

- message: Import outside toplevel (pylint.lint)
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T10:50:36
- ignored: because monkey patching

```
  295: def main(args: typ.Sequence[str] = sys.argv[1:]) -> ExitCode:
  ...
  301:         try:
  302:             # We don't want to load this code before the monkey patching is done.
> 303:             import pylint.lint
  304:
  305:             pylint.lint.Run(dec.pylint_run_args)
```


