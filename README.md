# Abantether Exchange Project

## Project Overview

This project is a cryptocurrency exchange platform that processes user purchase requests and buys cryptocurrencies in bulk from an external exchanger.

## Features

- **User Authentication**: JWT-based authentication system.
- **Order Management**: Users can place orders for purchasing cryptocurrencies.
- **Batch Processing**: Orders are grouped and processed in batches.
- **Exchange Transactions**: The platform interacts with external exchangers to complete transactions.
- **Task Queue**: Uses Redis and RQ for asynchronous processing.

## Project Structure

```
web-service/
  aban/
    asgi.py
    settings.py
    urls.py
    wsgi.py
  app/
    fixtures/
      cryptocurrency_fixture.json
      exchanger_fixture.json
      users_fixture.json
      userwallet_fixture.json
    management/
      commands/
        batch_maker_command.py
        queues_worker_command.py
    migrations/
      0001_initial.py
    models/
      __init__.py
      crypto_currency_model.py
      exchange_transaction_model.py
      exchanger_model.py
      exchanger_request_logs_model.py
      order_exchange_transaction_model.py
      order_model.py
      transaction_model.py
      user_wallet_model.py
    serializers/
      __init__.py
      purchase_serializer.py
      signup_serializer.py
    tasks/
      __init__.py
      settle_task.py
    tests/
      test_batch_maker_command.py
      test_purchase_view.py
      test_settle_task.py
    views/
      __init__.py
      auth_view.py
      purchase_view.py
    admin.py
    apps.py
    redis_client.py
    urls.py
  .env.example
  .gitignore
  Dockerfile
  manage.py
  requirements.txt
  schedules
.env.example
.gitignore
docker-compose.yaml
README.md
```

## Installation

### Prerequisites

- Python 3.x
- Django
- Redis
- Docker
- MySQL

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/alirezadp10/abantether.git
   cd abantether
   ```
2. Set up environment variables:
   ```bash
   cp .env.example .env
   cp web-service/.env.example web-service/.env
   ```
3. Apply migrations:
   ```bash
   python manage.py migrate
   ```
4. Run the server:
   ```bash
   docker-compose up --build
   ```

## Scheduled Tasks

The batch processing command is scheduled using cron:

```
* * * * * root /usr/local/bin/python /app/manage.py batch_maker_command >> /var/log/cron.log 2>&1
```

## API Endpoints

### Authentication

- **POST** `/api/signup/` - Register a new user.
- **POST** `/api/token/` - Obtain JWT token.

### Purchase

- **POST** `/api/purchase/` - Place an order to buy cryptocurrency.

## License

This project is licensed under the MIT License.

