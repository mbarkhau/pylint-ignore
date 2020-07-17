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

### Line 91 - R0902 (too-many-instance-attributes)

- message: Too many instance attributes (10/7)
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T09:59:24


```
  89:
  90:
> 91: class PylintIgnoreDecorator:
  92:     # NOTE (mb 2020-07-17): The term "Decorator" refers to the gang of four
  93:     #   pattern, rather than the typical usage in python which is about function
```


### Line 155 - W0511 (fixme)

- message: TODO (mb 2020-07-17): This will override any configuration, but it is not
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T11:39:54

```
  124:     def _parse_args(self, args: typ.List[str]) -> None:
  ...
  153:             arg_i += 1
  154:
> 155:         # TODO (mb 2020-07-17): This will override any configuration, but it is not
  156:         #   ideal. It would be better if we could use the same config parsing logic
  157:         #   as pylint and raise an error if anything other than jobs=1 is configured
```


### Line 196 - W0613 (unused-argument)

- message: Unused argument 'lineno'
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T09:59:24


```
  190:     def is_enabled_entry(
  ...
  194:         symbol  : str,
  195:         msg_text: str,
> 196:         lineno  : int,
  197:         srctxt  : catalog.MaybeSourceText,
  198:     ) -> bool:
```


### Line 277 - C0415 (import-outside-toplevel)

- message: Import outside toplevel (pylint.message.message_handler_mix_in.MessagesHandlerMixIn)
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T10:50:36

```
  273:     def monkey_patch_pylint(self) -> None:
  ...
  275:         #   found. Though I'm not quite sure why msg_descr that is a code would
  276:         #   imply that it's a candidate to generate output and otherwise not.
> 277:         from pylint.message.message_handler_mix_in import MessagesHandlerMixIn
  278:
  279:         self.pylint_is_message_enabled = MessagesHandlerMixIn.is_message_enabled
```


### Line 293 - C0415 (import-outside-toplevel)

- message: Import outside toplevel (pylint.lint)
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T10:50:36

```
  286: def main() -> ExitCode:
  ...
  291:     try:
  292:         # We don't want to load this code before the monkey patching is done.
> 293:         import pylint.lint
  294:
  295:         pylint.lint.Run(dec.pylint_run_args)
```


