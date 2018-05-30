# Contributing
There are several ways to contribute to the official Stregsystem github (not to be confused with the official new [Stregsystem](https://github.com/f-klubben/stregsystem)), we recommend reading this file to familiarise yourself with our guidelines.

If you were linked here from an issue please read the first subsection on writing a good issue.

## Suggest a feature
The volunteers love creating new features so if you have an idea for something cool the system could do, please feel free to suggest it.

A good feature request gives context for the feature and tells a short focused story about how the feature will be used.

### Short example
> ### Implement multibuy
> Customers often want to buy several beers in a row and the current workflow of typing in your username and then using to mouse to click on the product can be sometimes frustrating.
> I suggest the ability to enter `<username> <product id 1> <number of products sought>` thus making it possible to buy several products in one purchase.

## Patches welcome!
If you want to contribute code you should fork the project.

The project only strives to be Python 3 compliant.

### Coding standards
We try to adhere to `flake8` whenever possible. Mostly to avoid any
discussions about coding style.

You can run install `flake8` and run `flake8 --install-hook` to install
a pre-commit hook.

### Branches
 - `master`: The running code on the live system.
 - `next`: The set of changes which will be included in the next release.

### Using test data
In order to simplify development for all, we have included a test fixture.
To use it do the following:
1. `python manage.py migrate`
2. `python manage.py testserver stregsystem/fixtures/testdata.json`
3. ???
4. Profit

Admin panel: `http://127.0.0.1:8000/admin/`
Login: tester: treotreo

Stregsystem: `http://127.0.0.1:8000/1/`
User: tester

If you want your actions to be persisted when running in test mode you can run:

`python manage.py loaddata testdata`

and use `python manage runserver` for running your test server.
