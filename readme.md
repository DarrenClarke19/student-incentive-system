[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/uwidcit/flaskmvc)
<a href="https://render.com/deploy?repo=https://github.com/uwidcit/flaskmvc">
  <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render">
</a>

![Tests](https://github.com/uwidcit/flaskmvc/actions/workflows/dev.yml/badge.svg)

# Student Incentive System
A Flask MVC CLI application that gamifies student volunteerism by allowing students to log service hours, have them approved by staff, and earn accolades (badges). The system includes a leaderboard to promote engagement.


# Dependencies
* Python3/pip3
* Packages listed in requirements.txt

# Installing Dependencies
```bash
$ pip install -r requirements.txt
```

# Configuration Management


Configuration information such as the database url/port, credentials, API keys etc are to be supplied to the application. However, it is bad practice to stage production information in publicly visible repositories.
Instead, all config is provided by a config file or via [environment variables](https://linuxize.com/post/how-to-set-and-list-environment-variables-in-linux/).

## In Development

When running the project in a development environment (such as gitpod) the app is configured via default_config.py file in the App folder. By default, the config for development uses a sqlite database.

default_config.py
```python
SQLALCHEMY_DATABASE_URI = "sqlite:///temp-database.db"
SECRET_KEY = "secret key"
JWT_ACCESS_TOKEN_EXPIRES = 7
ENV = "DEVELOPMENT"
```

These values would be imported and added to the app in load_config() function in config.py

config.py
```python
# must be updated to inlude addtional secrets/ api keys & use a gitignored custom-config file instad
def load_config():
    config = {'ENV': os.environ.get('ENV', 'DEVELOPMENT')}
    delta = 7
    if config['ENV'] == "DEVELOPMENT":
        from .default_config import JWT_ACCESS_TOKEN_EXPIRES, SQLALCHEMY_DATABASE_URI, SECRET_KEY
        config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
        config['SECRET_KEY'] = SECRET_KEY
        delta = JWT_ACCESS_TOKEN_EXPIRES
...
```

## In Production

When deploying your application to production/staging you must pass
in configuration information via environment tab of your render project's dashboard.

![perms](./images/fig1.png)

# Flask Commands

wsgi.py is a utility script for performing various tasks related to the project. You can use it to import and test any code in the project. 
You just need create a manager command function, for example:

```python
# inside wsgi.py

user_cli = AppGroup('user', help='User object commands')

@user_cli.command("create", help="Creates a user")
@click.argument("username")
@click.argument("password")
@click.argument("role", type=click.Choice(['student', 'staff']))
def create_user_command(username, password, role):
    result = create_user(username, password, role)
    print(result["message"])

app.cli.add_command(user_cli) # add the group to the cli

```

Then execute the command invoking with flask cli with command name and the relevant parameters

```bash
$ flask user create bob bobpass <role>
```


# Running the Project

_For development run the serve command (what you execute):_
```bash
$ flask run
```

_For production using gunicorn (what the production server executes):_
```bash
$ gunicorn wsgi:app
```

# Deploying
You can deploy your version of this app to render by clicking on the "Deploy to Render" link above.

# Initializing the Database
When connecting the project to a fresh empty database ensure the appropriate configuration is set then file then run the following command. This must also be executed once when running the app on heroku by opening the heroku console, executing bash and running the command in the dyno.

```bash
$ flask init
```

# Database Migrations
If changes to the models are made, the database must be'migrated' so that it can be synced with the new models.
Then execute following commands using manage.py. More info [here](https://flask-migrate.readthedocs.io/en/latest/)

```bash
$ flask db init
$ flask db migrate
$ flask db upgrade
$ flask db --help
```

# CLI Commands

---

## 1. Authentication Commands

| Command | Description |
|--------|-------------|
| `flask auth login <username>` | Log in as an existing user and store session information. All existing student passwords are "studentpass". All existing staff passwords are "staffpass" |
| `flask auth current-user` | Display the currently logged-in user’s information (username + role). |
| `flask auth logout` | Log out and clear the current session. |

---

## 2. User management Commands

| Command | Description |
|--------|-------------|
| `flask user create <username> <password> <role>` | Create a new user. Roles can be `student` or `staff`. |
| `flask user list` | Show all users along with their profile info (ID, username, role, total hours if student). |

---

## 3. Student Service Commands

| Command | Description |
|--------|-------------|
| `flask service submit-hours <hours> --description "Helped at library"` | Submit a request for volunteer hours. Staff must later approve it. |
| `flask service my-requests` | View all of your submitted hour requests with their status (pending, approved, rejected). |
| `flask service my-logs` | View your confirmed (approved) service logs and total hours. |
| `flask service leaderboard --limit 5` | View the top students ranked by total confirmed hours (limit can be any number). |
| `flask service view-accolades` | View accolades (10h, 25h, 50h milestones) earned by the currently logged in student. |

---

## 4. Staff Review Commands

| Command | Description |
|--------|-------------|
| `flask service pending-students` | List all students with pending hour requests and their total pending hours. |
| `flask service review-hours <username>` | Enter interactive review mode for a specific student’s requests. You can approve or reject each request individually. |

# Testing

## Unit & Integration
Unit and Integration tests are created in the App/test. You can then create commands to run them. Look at the unit test command in wsgi.py for example

```python
@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "User"]))
```

You can then execute all user tests as follows

```bash
$ flask test user
```

You can also supply "unit" or "int" at the end of the comand to execute only unit or integration tests.

You can run all application tests with the following command

```bash
$ pytest
```

## Test Coverage

You can generate a report on your test coverage via the following command

```bash
$ coverage report
```

You can also generate a detailed html report in a directory named htmlcov with the following comand

```bash
$ coverage html
```

# Demo 
![Student-Incentive-System](https://github.com/user-attachments/assets/92e24066-f04d-4faf-89c6-9447be2e0233)

![Student-Incentive-System-2](https://github.com/user-attachments/assets/4d67b581-ba06-4968-acbb-a4a83285adca)



