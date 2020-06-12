# Slack Timeliner

## Setting

### Google Cloud Builds

```
gcloud beta builds triggers create github \
      --repo-owner="Owner" \
      --repo-name="slack-timeliner" --branch-pattern="^master$" \
      --build-config="cloudbuild.yaml" \
      --substitutions _SLACK_REPORT_CHANNEL="channel_name",_BQ_DATASET="ic_slack_data",_BQ_TABLE="timeliner"
```
