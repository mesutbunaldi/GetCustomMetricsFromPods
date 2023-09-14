# GetCustomMetricsFromPods

We are getting some special metrics from pods on init namespace

Also we are sending metrics to PushGateway , and we can pull these metrics from prometheus and visualize with grafana.

We have to deploy PushGateway somewhere on same cluster with the executing script or we have to make port-forward from the local machine.

İf we use a service object for PushGateway, we can access basically from anywhere on cluster.

In addition, if we use ServiceMonitor object for Prometheus, target will be defined automatically on Prometheus and we can pull these metrics from PushGateway.
