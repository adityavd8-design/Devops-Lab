# DevOps Lab

Hands-on DevOps lab exercises covering **Kubernetes (Minikube)**, **Docker networking and security**, **monitoring with Prometheus & Grafana** and **CI with Jenkins**.

Each exercise folder has the source files, a `README.md` with the steps I followed, the outputs / observations, issues I faced and how I fixed them, and a `screenshots/` folder.

## Exercises

| # | Exercise | Topics |
|---|----------|--------|
| 1 | [Kubernetes Getting Started - Hello Pod](Exercise-01-Kubernetes-Getting-Started/) | minikube, pod, NodePort service |
| 2 | [Deploy a Flask App on Minikube using kubectl and YAML](Exercise-02-Minikube-Kubectl-Flask/) | docker-env, Deployment, Service, imagePullPolicy |
| 3 | [Scaling a Flask App with ReplicaSets](Exercise-03-Minikube-Scaling-Flask-App-with-ReplicaSets/) | ReplicaSet, scaling, self healing, probes |
| 4 | [Docker Networking with Multiple Containers](Exercise-04-Docker-Networking/) | bridge network, Flask + MySQL + Redis, DNS by container name |
| 5 | [Docker Security with AppArmor and Python](Exercise-05-Docker-Security-AppArmor/) | AppArmor profile, Docker SDK for Python |
| 6 | [Real-Time Monitoring of a Quick Commerce App](Exercise-06-Grafana-Realtime-Monitoring/) | prometheus-client, Prometheus, alert rules, Grafana, Jenkins pipeline |
| 7 | [Introduction to CI and Jenkins Installation](Exercise-07-Jenkins-CI-Automation/) | CI concepts, Jenkins in Docker |
| 8 | [Jenkins Hello World Job](Exercise-08-Jenkins-Hello-World-Job/) | Freestyle job, Git SCM, shell build step |
| 9 | [Jenkins Multi-Stage Pipeline](Exercise-09-Jenkins-Multi-Stage-Pipeline/) | Jenkinsfile, Build / Test / Deploy stages |
| 10 | [Multi-Node Minikube Cluster with Multiple Apps](Exercise-10-Minikube-Multi-Node-Multi-App/) | 3 node cluster, pod anti-affinity, registry addon |

## Environment Used

| Tool | Version |
|------|---------|
| OS | Windows 11 + WSL2 (Ubuntu 26.04 LTS) |
| Editor | VS Code (WSL extension) |
| Docker Engine | 29.9.2 |
| Minikube | v1.39.0 (docker driver, docker container runtime) |
| kubectl | v1.37.1 |
| Kubernetes | v1.37.0 |
| Python | 3.14 (host), 3.8 / 3.9 / 3.11 (container images) |
| Jenkins | 2.580.1 LTS (Docker) |
| Prometheus | latest (Docker) |
| Grafana | v13.2.4 (Docker) |

### Setup notes
- Docker Engine was installed directly inside WSL Ubuntu (instead of using Docker Desktop) so that the exercises behave like a normal Linux machine - `docker0` is `172.17.0.1`, `--network=host` works, and AppArmor is enforced.
- AppArmor was enabled in the WSL kernel by adding `kernelCommandLine = apparmor=1 security=apparmor` to `%UserProfile%\.wslconfig` and mounting `securityfs`.
- Minikube was set to use the docker container runtime (`minikube config set container-runtime docker`) so that `eval $(minikube docker-env)` works.

