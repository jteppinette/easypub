# easypub.io

## Development

### Required Software

Refer to the links provided below to install these development dependencies:

- [direnv](https://direnv.net)
- [docker](https://docs.docker.com/)
- [git](https://git-scm.com/)
- [prettier](https://prettier.io/docs/en/install.html)
- [pyenv](https://github.com/pyenv/pyenv#installation)

### Getting Started

**Setup**

```sh
$ pyenv install 3.10.7
$ direnv allow
$ pip install -r requirements/dev.txt
$ pre-commit install
$ docker-compose up -d
```

**Tests**

_Run_

```sh
$ pytest
```

_Watch_

```sh
$ ptw
```

**Run**

The runserver command should only be used in development. In production, gunicorn should be used. This is described in a later section.

```sh
$ easypub runserver
```

```sh
$ open http://localhost:8000
```

## Usage

**Dependencies**

- Redis

**Environment Variables**

```
CACHE_URL
DEBUG=0
REQUEST_TIMEOUT=5
WEB_CONCURRENCY=1
```

**Compile Static Assets**

The provided `easypub collectstatic` needs to be ran before engaging the production server. This will compile all
static assets with the correct filename digest (required for proper caching).

```sh
$ easypub collectstatic
```

Notice, this is already included in the Heroku buildpack integration, so it is only necessary when performing a custom deployment.

**Server**

_We recommend using Gunicorn in production._

```sh
$ gunicorn --worker-class uvicorn.workers.UvicornWorker easypub.asgi:app
```

Notice, this is already included in the Heroku `Procfile`, so it is only necessary when performing a custom deployment.

## Deployment

### Heroku

```
$ heroku create
$ git push heroku master
```
