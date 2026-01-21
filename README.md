# ClickHouse Cloud Prometheus/Grafana mix-in

Pre-configured Grafana dashboard for monitoring ClickHouse Cloud services via the ClickHouse Cloud
[Prometheus API endpoint](https://clickhouse.com/docs/integrations/prometheus).

It also supports
[native ClickHouse Prometheus exporter](https://clickhouse.com/docs/operations/server-configuration-parameters/settings#prometheus).

## Links
- Dashboard in [Grafana dashboards marketplace](https://grafana.com/grafana/dashboards/23415-prom-exporter-instance-dashboard-v2/)
- Getting started guide in our [blog post](https://clickhouse.com/blog/monitor-with-new-prometheus-grafana-mix-in)

## BYOC Dashboard

The BYOC (Bring Your Own Cloud) dashboard is automatically generated from `dashboard.json` via GitHub Actions whenever changes are pushed to either `dashboard.json` or the converter script.

The CI workflow will:
- Convert `dashboard.json` to `dashboard_byoc.json`
- Automatically commit and push the generated file back to the repository
- Upload the generated dashboard as a workflow artifact for download

To manually generate the BYOC dashboard locally, run:

```shell
python3 .github/scripts/convert.py dashboard.json dashboard_byoc.json
```