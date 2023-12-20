# Yatube

## Tecnhologies

- Python 3.9.10
- Django 2.2.16
- SQLite3
-

## Description

A social network for publishing posts. The architecture is MVC. Pagination is used to display posts.
Caching and statics are configured. Authorization, registration, password change and recovery via email are implemented.
Tests were also written.

### To deploy this project need the next actions

- Download project with SSH

```text
git clone git@github.com:Zulusssss/hw05_final.git
```

- Create and activate virtual environment

```text
For Windows:
py -3.9.10 -m venv venv
source venv/Scripts/activate
For Linux:
python3.9.10 -m venv venv
source venv/Scripts/bin
For macOS:
brew unlink python@<default_version_python>
brew link python@3.9.10
```

- Creating and performing migrations for a database

```text
python manage.py makemigrations
python manage.py migrate
```

- Run the project

```text
python manage.py runserver
```

### *Backend by:*

[Zulusssss](https://github.com/Zulusssss)
