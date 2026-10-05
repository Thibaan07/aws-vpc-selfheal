import time
import urllib.request

import boto3

REGION = "us-east-1"
ALARM = "selfheal-instance-reboot"
INSTANCE_NAME = "tf-web-server"

ec2 = boto3.client("ec2", region_name=REGION)
cw = boto3.client("cloudwatch", region_name=REGION)


def find_ip():
    resp = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [INSTANCE_NAME]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )
    for r in resp["Reservations"]:
        for i in r["Instances"]:
            return i.get("PublicIpAddress")
    return None


def page_ok(ip):
    try:
        with urllib.request.urlopen(f"http://{ip}", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def alarm_state():
    return cw.describe_alarms(AlarmNames=[ALARM])["MetricAlarms"][0]["StateValue"]


def clock(t):
    return time.strftime("%H:%M:%S", time.localtime(t)) + f".{int((t % 1) * 1000):03d}"


ip = find_ip()
if not ip:
    raise SystemExit("no running server found")

print("waiting until the page is up and the alarm is not in ALARM...")
start_wait = time.time()
while not (page_ok(ip) and alarm_state() != "ALARM"):
    if time.time() - start_wait > 300:
        raise SystemExit("alarm still in ALARM after 300 s, try again later")
    time.sleep(5)

print("ready, forcing the alarm")
t0 = time.time()
cw.set_alarm_state(AlarmName=ALARM, StateValue="ALARM", StateReason="Manual test")

down = None
up = None
while time.time() - t0 < 300:
    ok = page_ok(ip)
    now = time.time()
    if not ok and down is None:
        down = now
    if ok and down is not None:
        up = now
        break
    time.sleep(0.5)

print(f"force time      {clock(t0)}")
if down is None:
    print("no outage seen, so no reboot happened")
elif up is None:
    print(f"page went down  {clock(down)}")
    print("page did not come back within 300 s")
else:
    print(f"page went down  {clock(down)}")
    print(f"page back up    {clock(up)}")
    print(f"downtime        {up - down:.1f} s")
    print(f"force to back   {up - t0:.1f} s")
