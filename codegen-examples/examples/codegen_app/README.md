# Codegen App

Simple example of running a codegen app.

## Run Locally

Spin up the server:

```
codegen serve
```

Spin up ngrok

```
ngrok http 8000
```

Go to Slack [app settings](https://api.slack.com/apps/A08CR9HUJ3W/event-subscriptions) and set the URL for event subscriptions

```
{ngrok_url}/slack/events
```

## Deploy to Modal

This will deploy it as a function

```
modal deploy app.py
```

Then you can swap in the modal URL for slack etc.
