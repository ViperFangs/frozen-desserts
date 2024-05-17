import pulumi
from pulumi_aws import ec2, s3

# Create an S3 bucket
bucket = s3.Bucket('frozen-desserts-bucket')

# Create a security group for the EC2 instance
security_group = ec2.SecurityGroup('web-secgrp',
    description='Enable HTTP and HTTPS access',
    ingress=[
        {'protocol': 'tcp', 'from_port': 80, 'to_port': 80, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': 'tcp', 'from_port': 443, 'to_port': 443, 'cidr_blocks': ['0.0.0.0/0']}
    ],
    egress=[
        {'protocol': '-1', 'from_port': 0, 'to_port': 0, 'cidr_blocks': ['0.0.0.0/0']}
    ])

# Get the latest Amazon Linux 2 AMI
ami = ec2.get_ami(most_recent=True,
                  owners=["amazon"],
                  filters=[{"name": "name", "values": ["amzn2-ami-hvm-*-x86_64-gp2"]}])

# Create an EC2 instance
server = ec2.Instance('web-server-www',
    instance_type='t2.micro',
    security_groups=[security_group.name],
    ami=ami.id,
    user_data='''#!/bin/bash
    sudo yum update -y
    sudo yum install -y ruby
    sudo yum install -y git
    sudo yum install -y httpd
    sudo systemctl start httpd
    sudo systemctl enable httpd

    # Install Rails and Bundler
    gem install rails bundler

    # Clone the application repo
    git clone https://github.com/viperfangs/frozen-desserts.git /var/www/frozen-desserts

    # Set up the application
    cd /var/www/frozen-desserts
    bundle install
    rails db:create
    rails db:migrate

    # Start the Rails server
    rails server -b 0.0.0.0
    ''',
    tags={"Name": "frozen-desserts-server"})

# Export the public IP and DNS of the instance
pulumi.export('publicIp', server.public_ip)
pulumi.export('publicHostName', server.public_dns)
