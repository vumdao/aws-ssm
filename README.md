## Amazon Simple Systems Manager (SSM)

####AWS Systems Manager is a collection of capabilities that helps you automate management tasks. This post describe how to send command to an EC2 instance using python boto3

![Alt Text](https://dev-to-uploads.s3.amazonaws.com/i/s2opxjyg5wt5voxat0mg.png)

###**1. Systems Manager prerequisites**
####1.1 Install SSM agent
- SSM Agent is installed, by default, on the following EC2 instances and Amazon Machine Images (AMIs):
 - Amazon Linux
 - Amazon Linux 2
 - Amazon Linux 2 ECS-Optimized AMIs
 - Ubuntu Server 16.04, 18.04, and 20.04

- There's manual way to install it [Manually install SSM Agent on EC2 instances for Linux](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-manual-agent-install.html)

- How to check if the instance installed SSM agent
```
dev:/home/ubuntu# systemctl status snap.amazon-ssm-agent.amazon-ssm-agent.service
● snap.amazon-ssm-agent.amazon-ssm-agent.service - Service for snap application amazon-ssm-agent.amazon-ssm-agent
   Loaded: loaded (/etc/systemd/system/snap.amazon-ssm-agent.amazon-ssm-agent.service; enabled; vendor preset: enabled)
   Active: active (running) since Thu 2020-11-19 20:47:31 UTC; 4 weeks 1 days ago
 Main PID: 27709 (amazon-ssm-agen)
    Tasks: 23 (limit: 4915)
   CGroup: /system.slice/snap.amazon-ssm-agent.amazon-ssm-agent.service
           ├─27709 /snap/amazon-ssm-agent/2996/amazon-ssm-agent
           └─27837 /snap/amazon-ssm-agent/2996/ssm-agent-worker
```

####1.2 Setup IAM role so that user/client install have SSM permission
```
        {
            "Effect": "Allow",
            "Action": [
                "ssm:*"
            ],
            "Resource": [
                "arn:aws:ec2:us-east-1:123456789012:instance/*"
            ]
        }
```
![Alt Text](https://dev-to-uploads.s3.amazonaws.com/i/wuh5uhc91izft7vv6cw7.png)
###2. Using boto3 to send SSM command
- The code using tag key-value to get dynamic instances target, so create tag for target instance
![Alt Text](https://dev-to-uploads.s3.amazonaws.com/i/fbrz600nq7z3brv69r0h.png)

- [ssm-send-cmd.py](https://github.com/vumdao/aws-ssm/blob/master/ssm-send-cmd.py)
```
import boto3
import time


def send_cmd(region):
    """ Use describe instance information to get instance id base on region """
    ssm_filter = [{'Key': 'tag:SSM', 'Values': ['ssm-cmd']}]
    ssm = boto3.client('ssm', region_name=region)
    instance_info = ssm.describe_instance_information(Filters=ssm_filter).get('InstanceInformationList', {})[0]
    instance_id = instance_info.get('InstanceId', '')
    cmd1 = "echo 'Start running services'"
    cmd2 = 'whoami'
    response = ssm.send_command(InstanceIds=[instance_id],
                                DocumentName='AWS-RunShellScript',
                                Parameters={"commands": [cmd1, cmd2]}
                                )
    command_id = response.get('Command', {}).get("CommandId", None)
    while True:
        """ Wait for SSM response """
        response = ssm.list_command_invocations(CommandId=command_id, Details=True)
        """ If the command hasn't started to run yet, keep waiting """
        if len(response['CommandInvocations']) == 0:
            time.sleep(1)
            continue
        invocation = response['CommandInvocations'][0]
        if invocation['Status'] not in ('Pending', 'InProgress', 'Cancelling'):
            break
        time.sleep(1)
    command_plugin = invocation['CommandPlugins'][-1]
    output = command_plugin['Output']
    print(f"Complete running, output: {output}")


send_cmd('us-east-1')
```

- Run
```
~/⚡ $ python ssm-send-cmd.py
Complete running, output: Start running services
root
```
