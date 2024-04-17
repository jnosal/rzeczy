## API Setup

``` bash
cd api
python3.11 -m venv .venv
pip install -r requirements-dev.txt
npm install
```

## Python virtualenv context
```bash
# it's important to have virtualenv activated, with one of two methods
. .venv/bin/activate
# or
source .venv/bin/activate
```

## Running API locally

``` bash
# run tests locally
make test

# tests locally with coverage
make test-cov

# run locally
docker-compose up localstack
./localstack.sh
make run

# query API
curl -X GET localhost:4000/api/status
curl -X GET localhost:4000/api/tasks/123/status
curl -X POST localhost:4000/api/tasks/schedule -H 'Content-Type: application/json' -d '{"task_name":"Leo","task_params":{}}'


# invoke jobs handler locally from script (assuming virtualenv active)
DEFAULT_AWS_REGION=us-east-1 DEFAULT_LOCALSTACK_URL=http://localhost:4566 python -m src.handlers.tasks.jobs

# invoke expire jobs results handler locally from script (assuming virtualenv active)
DEFAULT_AWS_REGION=us-east-1 DEFAULT_LOCALSTACK_URL=http://localhost:4566 python -m src.handlers.tasks.jobs_results_expire


# endpoints locally wherever sqs handler is necessary try to run job in corresponding handler by generating custom SQS payload
# in order for use_localstack to be true DEFAULT_LOCALSTACK_URL must be defined and ENV_NAME must be 'local'
# so that tests do not trigger that logic

if settings.use_localstack:
    from ..handlers.tasks.jobs import async_handler as executor
    from ..handlers.tasks.jobs import get_sqs_mock_data

    await executor(*get_sqs_mock_data(**message))
```