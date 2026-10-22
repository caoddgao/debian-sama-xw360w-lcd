# netfleece

Pure Python MS-NRBF reader, version 0.1.3.1, obtained from
[PyPI](https://pypi.org/project/netfleece/). Wheel SHA-256:
`8c6e31d85166b433a8c782decff333f14976ce739fe04117a81ce6cd2973bfea`.
MIT license in `LICENSE`.

Only the `valuedispatch` helper was adapted for Python 3.13: recent
`functools.singledispatch` rejects enum values as registration keys.
This library is used by the offline theme importer. The display service does
not parse `.turtheme` files at runtime.
