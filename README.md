Stregsystemet [![Django CI Actions Status](https://github.com/f-klubben/stregsystemet/workflows/Django%20CI/badge.svg)](https://github.com/f-klubben/stregsystemet/actions)  [![codecov](https://codecov.io/gh/f-klubben/stregsystemet/branch/next/graph/badge.svg)](https://codecov.io/gh/f-klubben/stregsystemet) 
========

This is the current stregsystem in the F-Klub.

Branches
-------
 - `master`: The running code on the live system.
 - `next`: The set of changes which will be included in the next release.

Python Environment
-------
For windows using Anaconda and virtual environments:
1. Download and install Anaconda
2. In a shell:
  - `conda create -n stregsystem python=3.11`
  - `activate stregsystem`
  - `pip install -r requirements.txt`
3. ???
4. Profit

For Ubuntu with virtual envs:
1. Install python3 with pip
 - `sudo apt install python3 python3-pip python3-venv`
2. Create virtual environment
 - `python3 -m venv venv`
3. Activate virtualenv
 - `source venv/bin/activate`
4. Install packages
 - `pip3 install -r requirements.txt`
5. ???
6. Profit

For systems running the Nix package manager:
1. Configure Nix to use nix-command and flakes
 - `echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf`
2. Start shell
 - `nix develop`
2. Or run the system
 - `nix run . testserver stregsystem/fixtures/testdata.json`
3. ???
4. Profit

For Mac users with virtual envs:
1. Install python3.11 with pip
 - `brew install python@3.11`
2. Create virtual environment
 - `python -m venv venv`
3. Activate virtualenv
 - `source venv/bin/activate`
4. Install packages
 - `pip install -r requirements.txt`
5. ???
6. Profit

Using Testdata
--------
In order to simplify development for all, we have included a test fixture.
Using `testserver` will delete the data after running.
To use it do the following:
1. `python manage.py migrate`
2. `python manage.py testserver stregsystem/fixtures/testdata.json`
3. ???
4. Profit

Admin panel: <http://127.0.0.1:8000/admin/>  
Login: `tester:treotreo`

Stregsystem: <http://127.0.0.1:8000/1/>  
There are different members that help you test different things:
| Member | Superpower |
|---|---|
| tester | Default test profile |
| q | Has short name for maximum testing speed |
| nodough | Has no stregdollars |
| lowdough | Only has 15 stregdollars |

Persistent Testdata
-------
Using `runserver` will automatically reload django on code change, and persist data in the database configured in `local.cfg` (can be whatever backend you want to use).
First time:
1. `python manage.py migrate`
2. `python manage.py loaddata stregsystem/fixtures/testdata.json`
3. `python manage.py runserver`
4. ???
5. Profit

From then on
1. `python manage.py runserver`
2. ???
3. Profit

Testing Mailserver
-------
Using the debugging tool [MailHog](https://github.com/mailhog/MailHog) (Follow their README for install instructions) and test the mailserver like this:
1. `MailHog --smtp-bind-addr 127.0.0.1:25`
2. Go to [http://127.0.0.1:8025](http://127.0.0.1:8025) in your browser
3. `python manage.py runserver`
4. ???
5. Profit

Themes
-------
[Read more about themes here.](./themes.md)

Achievements
-------
[Read more about achievements here.](./achievements.md)
