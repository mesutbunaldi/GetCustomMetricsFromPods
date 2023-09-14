from prometheus_client import Gauge, CollectorRegistry, push_to_gateway

# Örnek pod adları
pod_names = ['pod1', 'pod2', 'pod3', 'pod4', 'pod5']

# CollectorRegistry ile yeni bir koleksiyon oluşturun
registry = CollectorRegistry()

# Her bir pod için Gauge metriklerini oluşturun ve sözlüğe ekleyin
for pod_name in pod_names:
    initialized_metric = Gauge('pod_initialized_{}'.format(pod_name), 'Initialized timestamp for pod {}'.format(pod_name), registry=registry)
    ready_metric = Gauge('pod_ready_{}'.format(pod_name), 'Ready timestamp for pod {}'.format(pod_name), registry=registry)
    containers_ready_metric = Gauge('pod_containers_ready_{}'.format(pod_name), 'Containers ready timestamp for pod {}'.format(pod_name), registry=registry)
    creation_time_metric = Gauge('pod_creation_time_{}'.format(pod_name), 'Creation timestamp for pod {}'.format(pod_name), registry=registry)

# Her bir pod için zaman damgalarını ayarlayın (örnek olarak, rasgele değerler)
import random
import time

for pod_name in pod_names:
    current_time = time.time()
    initialized_metric.set(current_time - random.randint(0, 60))
    ready_metric.set(current_time - random.randint(0, 60))
    containers_ready_metric.set(current_time - random.randint(0, 60))
    creation_time_metric.set(current_time - random.randint(0, 60))

# Metrikleri Pushgateway'e gönderin
push_to_gateway('http://localhost:9091', job='pod_metrics_job', registry=registry)
