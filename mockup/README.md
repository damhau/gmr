# Morning routine (Flic Hub -> Raspberry Pi)

## Install on the Pi
    pip install -r requirements.txt
    uvicorn server:app --host 0.0.0.0 --port 8000
(wrap it in a systemd unit so it starts on boot)

## Flic Hub config
For each button, Click -> "Internet Request":
  Method: POST   URL: http://<pi-ip>:8000/event
  Content-Type: application/json
  Body: {"task":"wake"}          (wake | clothes | breakfast | teeth)
Optional: Double click -> {"task":"wake","action":"undo"}
          Hold         -> {"task":"wake","action":"skip"}

## Use
Open http://<pi-ip>:8000 on a tablet or phone.
Edit TASKS / GOAL_TIME / TZ at the top of server.py.
