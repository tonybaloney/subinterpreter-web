# Sub-interpreter Web Extension for Hypercorn

This is an experimental web extension for Hypercorn that allows for workers to be started inside sub interpreters 
instead of Python processes using the multiprocessing module.

The purpose is to demonstrate the feasibility of running multiple workers in a single process, and to provide a test
mechanism for web frameworks' compatibility with sub interpreters.

## Usage

```console
$ python microweb.py -w 4 my_app:app
```

## Limitations

- The extension is experimental and should not be used in production.
- Hypercorn configuration is not serializable between interpreters, so it's currently only copying the app path and worker count
