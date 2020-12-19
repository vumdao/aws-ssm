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
