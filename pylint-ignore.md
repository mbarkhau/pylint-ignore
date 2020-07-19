# `pylint-ignore`

**WARNING: This file is programatically generated. You should not
edit this file manually.**

This file is parsed by `pylint-ignore` to determine which `pylint`
messages should be ignored.

The recommended approach to using `pylint-ignore` is:

- If a message refers to a valid issue, update your code rather than
  ignoring the message.
- If a message should *always* be ignored (globally), then to do so
  via the usual `pylintrc` or `setup.cfg` files rather than this
 `pylint-ignore.md` file.
- If a message is a false positive, add a comment of this form to your code:
  `# pylint:disable=<symbol> ; explanation why this is a false positive`


## File src/pylint_ignore/__main__.py - Line 190 - W0511 (fixme)

- `message: TODO (mb 2020-07-17): This will override any configuration, but it is not`
- `author : Manuel Barkhau <mbarkhau@gmail.com>`
- `date   : 2020-07-17T11:39:54`

```
  153:     def _init_from_args(self, args: typ.Sequence[str]) -> None:
  ...
  188:             raise SystemExit(USAGE_ERROR)
  189:
> 190:         # TODO (mb 2020-07-17): This will override any configuration, but it is not
  191:         #   ideal. It would be better if we could use the same config parsing logic
  192:         #   as pylint and raise an error if anything other than jobs=1 is configured
```


