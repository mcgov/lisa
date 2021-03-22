# command line reference

- [common arguments](#common-arguments)
  - [-d, --debug](#-d---debug)
  - [-r, --runbook](#-r---runbook)
  - [-h, --help](#-h---help)
  - [-v, --variable](#-v---variable)
- [run](#run)
- [check](#check)
- [list](#list)

## common arguments

### -d, --debug
Set log level to debug, by default it is info level.

```sh
lisa -d
lisa --debug
```
### -r, --runbook
Path of runbook, it can be full path or absolute path, most of commands need specify the runbook, and only can be specified once.

```sh
lisa -r .\microsoft\runbook\azure.yml
```
### -h, --help
Show this help message and exit.

```sh
lisa -h
lisa --help
```
### -v, --variable
Define one or more variables with 'NAME:VALUE', it will overwrite value in yml file.

```sh
lisa -v location:westus2 gallery_image 'Canonical UbuntuServer 18.04-LTS Latest' -r .\microsoft\runbook\azure.yml
```
## run
Run with yml file, it has the same effect without specifing this argument.

```sh
lisa run -r .\microsoft\runbook\azure.yml
```
## check
Check specified yml file is vaild or not.

```sh
lisa check -r .\microsoft\runbook\azure.yml
```
## list
List cases in specified yml file, list must be used with -t argument, currently the only vaild choice for -t/--type is case.

```sh
lisa list -t case -r .\microsoft\runbook\azure.yml
```