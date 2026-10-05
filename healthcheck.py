import sys
import time
import urllib.request

import boto3

REGION = "us-east-1"
TOPIC_ARN = "arn:aws:sns:us-east-1:589458396976:selfheal-alerts"
INSTANCE_NAME = "tf-web-server"  # the Name tag set in main.tf
INTERVAL = 10  # seconds between checks (state this number on the resume)

ec2 = boto3.client("ec2", region_name=REGION)
ssm = boto3.client("ssm", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)


def ts():
    return time.strftime("%H:%M:%S")


def find_server():
    """Find the running server by its Name tag. Returns (instance_id, public_ip)."""
    resp = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [INSTANCE_NAME]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )
    for reservation in resp["Reservations"]:
        for inst in reservation["Instances"]:
            return inst["InstanceId"], inst.get("PublicIpAddress")
    return None, None


def page_ok(ip):
    """True if the web page answers with HTTP 200 within 5 seconds."""
    try:
        with urllib.request.urlopen(f"http://{ip}", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def restart_httpd(instance_id):
    """Ask SSM to run 'systemctl restart httpd' on the server."""
    ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": ["systemctl restart httpd"]},
    )


def notify(subject, message):
    sns.publish(TopicArn=TOPIC_ARN, Subject=subject, Message=message)


def check_once():
    instance_id, ip = find_server()
    if not instance_id or not ip:
        print(f"{ts()} no running server named {INSTANCE_NAME} found")
        return False

    if page_ok(ip):
        print(f"{ts()} healthy")
        return True

    print(f"{ts()} page DOWN, restarting httpd via SSM")
    start = time.time()
    restart_httpd(instance_id)

    while time.time() - start < 120:
        time.sleep(2)
        if page_ok(ip):
            secs = round(time.time() - start, 1)
            print(f"{ts()} recovered {secs}s after detection")
            notify(
                "Selfheal: web page recovered",
                f"Page was down. Restarted httpd via SSM. Recovered in {secs} seconds.",
            )
            return True

    notify(
        "Selfheal: recovery FAILED",
        "Page still down 120 seconds after restarting httpd. Needs a human.",
    )
    print(f"{ts()} recovery FAILED")
    return False


def main():
    if "--loop" in sys.argv:
        while True:
            check_once()
            time.sleep(INTERVAL)
    return 0 if check_once() else 1


if __name__ == "__main__":
    sys.exit(main())
