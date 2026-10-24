# Exercise 6 - Real-Time Operations Monitoring and Alerting (Prometheus + Grafana + Jenkins)

## Objective
As a DevOps engineer at ZAPPTTO (a quick delivery service), build a monitoring setup that gives real-time insight into delivery performance:
- a Python app that simulates delivery metrics
- Prometheus to scrape the metrics and evaluate alert rules
- Grafana dashboards to visualise them
- a Jenkins pipeline to build and run everything with Docker

## Directory Structure
```
delivery_monitoring/
├── delivery_metrics.py      # Python script to simulate metrics
├── prometheus.yml           # Prometheus configuration
├── alert_rules.yml          # Alert rules
├── Dockerfile               # Image for delivery_metrics (used by the pipeline)
├── Jenkinsfile              # Jenkins pipeline
└── grafana-dashboard.json   # Grafana dashboard (4 panels)
```

## Environment
- WSL2 Ubuntu 26.04, Docker Engine 29.9.2 (docker0 = `172.17.0.1`)
- Python 3.14, prometheus-client
- Prometheus (prom/prometheus), Grafana v13.2.4, Jenkins 2.580.1

---

## Step 1 - Run the Python application
```bash
python3 -m venv venv && source venv/bin/activate
pip3 install prometheus-client
nohup python3 delivery_metrics.py > metrics.log 2>&1 &
tail -n 15 metrics.log
```
Ubuntu 26.04 does not allow `pip install` into the system Python (PEP 668), so I used a virtual environment. I ran the script in the background with `nohup` because it prints every second.

![run delivery metrics](screenshots/01-run-delivery-metrics.png)

Metrics endpoint (created automatically by `start_http_server(8000)`):
```bash
curl -s http://localhost:8000/metrics | grep deliver
```
![curl metrics](screenshots/02-curl-metrics-endpoint.png)

## Step 2 - Configure and run Prometheus
`prometheus.yml` scrapes Prometheus itself and the delivery service on the docker0 IP `172.17.0.1:8000`, and loads `alert_rules.yml`:
- **HighPendingDeliveries** - `pending_deliveries > 10` for 15s (warning)
- **HighAverageDeliveryTime** - `average_delivery_time_sum / average_delivery_time_count > 30` (critical)

```bash
ip addr show docker0
docker run -d --name prometheus --network=host \
  -v ./prometheus.yml:/etc/prometheus/prometheus.yml \
  -v ./alert_rules.yml:/etc/prometheus/alert_rules.yml prom/prometheus
docker ps -a | grep prom
```
![run prometheus](screenshots/03-run-prometheus.png)

Prometheus UI at http://localhost:9090 - query `pending_deliveries`:

![prometheus query](screenshots/04-prometheus-query-pending-deliveries.png)

**Status → Targets** - both targets are UP:

![prometheus targets](screenshots/05-prometheus-targets-up.png)

**Alerts** page:

![prometheus alerts](screenshots/06-prometheus-alerts.png)

## Step 3 - Set up Grafana
```bash
docker run -d --name grafana -p 3000:3000 grafana/grafana
```
![run grafana](screenshots/07-run-grafana.png)

Logged in at http://localhost:3000 with `admin / admin` and skipped the password change.

![grafana login](screenshots/08-grafana-login.png)
![grafana home](screenshots/09-grafana-home.png)

### Add Prometheus as a data source
Connections → Data sources → Add data source → Prometheus → URL `http://172.17.0.1:9090` → **Save & test**

![add data source](screenshots/10-grafana-add-data-source.png)
![prometheus url](screenshots/11-grafana-prometheus-url.png)
![save and test](screenshots/12-grafana-datasource-save-test-success.png)

### Delivery monitoring dashboard
Panels:
1. Total Deliveries - `total_deliveries`
2. Pending Deliveries - `pending_deliveries` (red threshold line at 10)
3. On-the-Way Deliveries - `on_the_way_deliveries`
4. Average Delivery Time - `average_delivery_time_sum / average_delivery_time_count` (red above 30s)

I saved the dashboard as JSON ([grafana-dashboard.json](delivery_monitoring/grafana-dashboard.json)) so it can be recreated, and loaded it through the Grafana HTTP API:
```bash
curl -s -u admin:admin -H "Content-Type: application/json" -X POST \
  http://localhost:3000/api/dashboards/db -d @grafana-dashboard.json
```
![import dashboard](screenshots/13-import-dashboard-api.png)
![delivery dashboard](screenshots/14-grafana-delivery-dashboard.png)

## Step 4 - Simulate alerts
Changed the pending range in `delivery_metrics.py` so it always crosses the threshold:
```python
pending = random.randint(50, 100)  # Increase range to exceed alert threshold
```
![vscode pending range](screenshots/15-vscode-increase-pending-range.png)

Restarted the script and Prometheus:
```bash
pkill -f delivery_metrics.py
nohup python3 delivery_metrics.py > metrics.log 2>&1 &
docker restart prometheus
```
![restart for alerts](screenshots/16-simulate-alerts-restart.png)

After about a minute **HighPendingDeliveries** is FIRING in Prometheus:

![alerts firing](screenshots/17-prometheus-alerts-firing.png)

And the Pending Deliveries panel in Grafana jumps above 50:

![dashboard high pending](screenshots/18-grafana-dashboard-high-pending.png)

## Step 5 - Jenkins pipeline
The pipeline (from Exercise 7's Jenkins) builds the `delivery_metrics` image and runs the app, Prometheus and Grafana as containers.

Things I had to set up for this to work:
1. Jenkins runs in Docker, so it needs the Docker CLI and access to the host Docker daemon. The Docker socket was already mounted when I started Jenkins; I copied the `docker` CLI and the `buildx` plugin into the container.
2. The exercise's Jenkinsfile builds an image with `docker build .` but there was no Dockerfile, so I added a small [Dockerfile](delivery_monitoring/Dockerfile).
3. `localSourcePath` in the *Setup Workspace* stage was set to `/var/jenkins_home/delivery_monitoring` and I copied the files there.
4. Because `/var/jenkins_home` is bind mounted at the same path on the host, the `-v $WORKSPACE/prometheus.yml:...` volume paths in the pipeline also exist on the host Docker daemon.
5. Added `docker rm -f ... || true` before `docker run` so the pipeline can be re-run without "container name already in use" errors.

```bash
pkill -f delivery_metrics.py
docker cp $(which docker) jenkins:/usr/bin/docker
docker exec -u root jenkins mkdir -p /usr/libexec/docker/cli-plugins
docker cp /usr/libexec/docker/cli-plugins/docker-buildx jenkins:/usr/libexec/docker/cli-plugins/docker-buildx
sudo mkdir -p /var/jenkins_home/delivery_monitoring
sudo cp delivery_metrics.py prometheus.yml alert_rules.yml Dockerfile /var/jenkins_home/delivery_monitoring/
```
![jenkins docker cli](screenshots/19-jenkins-docker-cli-and-push.png)

New Item → `Delivery-Monitoring-Pipeline` → Pipeline, and pasted the Jenkinsfile into the **Pipeline script** box:

![new pipeline job](screenshots/20-jenkins-new-pipeline-job.png)
![pipeline script pasted](screenshots/21-jenkins-pipeline-script-pasted.png)

Build #1 - SUCCESS:

![pipeline success](screenshots/22-jenkins-pipeline-success.png)

Stages - Pre-check Docker → Setup Workspace → Build Docker Image → Run Application → Run Prometheus & Grafana:

![pipeline stages](screenshots/23-jenkins-pipeline-stages.png)
![console output](screenshots/24-jenkins-console-output.png)

Containers started by the pipeline, metrics endpoint and Prometheus targets:
```bash
docker ps
curl -s http://localhost:8000/metrics | grep -E "^(total|pending|on_the_way)_deliveries"
curl -s http://localhost:9090/api/v1/targets
```
![pipeline containers running](screenshots/25-pipeline-containers-running.png)

## Expected Outputs - Checklist
| Expected output | Done |
|-----------------|------|
| Metrics endpoint http://localhost:8000/metrics | ✅ |
| Prometheus graphs for the delivery metrics | ✅ |
| Grafana dashboard with the 4 panels | ✅ |
| Jenkins logs with a successful pipeline build | ✅ |
| Prometheus alerts for high pending deliveries | ✅ |

## Observations
- `average_delivery_time` is a Summary, so Prometheus stores `_sum` and `_count`; dividing them gives the average since the app started, which stays around 30s (random value between 15 and 45). That is why the HighAverageDeliveryTime alert keeps switching between firing and inactive.
- With `--network=host` Prometheus can reach the app on the docker0 address `172.17.0.1`, and Grafana (bridge network) reaches Prometheus on the same address.

## Conclusion
A complete monitoring pipeline was built: Python app → Prometheus (scraping + alert rules) → Grafana dashboard, with alerts firing when pending deliveries go above the threshold, and the whole stack can also be deployed with a Jenkins pipeline.
