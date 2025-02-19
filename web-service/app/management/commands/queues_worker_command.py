from django.core.management.base import BaseCommand
from app.models import CryptoCurrency
from rq import Worker, Queue
from app.redis_client import RedisClient


class Command(BaseCommand):
    help = "This command will process the queues"

    def handle(self, *args, **options):
        listen = ['default']
        listen += CryptoCurrency.objects.values_list('symbol', flat=True)

        redis_client = RedisClient()
        conn = redis_client.client

        queues = [Queue(name=q, connection=conn) for q in listen]
        worker = Worker(queues, connection=conn)
        worker.work()
