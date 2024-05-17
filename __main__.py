import pulumi
from pulumi_aws import ec2, s3

# Create an S3 bucket
bucket = s3.Bucket('frozen-desserts-bucket')

# Create a security group for the EC2 instance
security_group = ec2.SecurityGroup('frozen-desserts-secgrp',
    description='Enable HTTP access',
    ingress=[
        {'protocol': 'tcp', 'from_port': 80, 'to_port': 80, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': 'tcp', 'from_port': 443, 'to_port': 443, 'cidr_blocks': ['0.0.0.0/0']}
    ])

# Create an EC2 instance
ami = ec2.get_ami(most_recent=True,
                  owners=["amazon"],
                  filters=[{"name": "name", "values": ["amzn2-ami-hvm-*-x86_64-gp2"]}])

server = ec2.Instance('frozen-desserts-server',
    instance_type='t2.micro',
    security_groups=[security_group.name],
    ami=ami.id,
    user_data='''#!/bin/bash
    sudo yum update -y
    sudo yum install -y ruby
    sudo yum install -y httpd
    sudo systemctl start httpd
    sudo systemctl enable httpd
    ''',
    tags={"Name": "web-server"})

# Export the public IP and DNS of the instance
pulumi.export('publicIp', server.public_ip)
pulumi.export('publicHostName', server.public_dns)
