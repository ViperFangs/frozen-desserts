import pulumi
from pulumi_aws import ec2, s3

# Create an S3 bucket
bucket = s3.Bucket('frozen-desserts-bucket')

# Create a security group for the EC2 instance
security_group = ec2.SecurityGroup('web-secgrp',
    description='Enable HTTP, HTTPS, and SSH access',
    ingress=[
        {'protocol': 'tcp', 'from_port': 80, 'to_port': 80, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': 'tcp', 'from_port': 443, 'to_port': 443, 'cidr_blocks': ['0.0.0.0/0']},
        {'protocol': 'tcp', 'from_port': 22, 'to_port': 22, 'cidr_blocks': ['0.0.0.0/0']}
    ],
    egress=[
        {'protocol': '-1', 'from_port': 0, 'to_port': 0, 'cidr_blocks': ['0.0.0.0/0']}
    ])

# Get the latest Amazon Linux 2 AMI
ami = ec2.get_ami(most_recent=True,
                  owners=["amazon"],
                  filters=[{"name": "name", "values": ["amzn2-ami-hvm-*-x86_64-gp2"]}])

# User data script to set up the server
user_data = r'''#!/bin/bash
sudo yum update -y
sudo amazon-linux-extras install nginx1 -y
sudo yum install -y ruby git

# Install Rails and Bundler
gem install rails bundler

# Clone the application repository
sudo git clone https://github.com/viperfangs/frozen-desserts.git /var/www/frozen-desserts

# Set up the application
cd /var/www/frozen-desserts
sudo bundle install
sudo yarn install
sudo RAILS_ENV=production rails db:create
sudo RAILS_ENV=production rails db:migrate
sudo RAILS_ENV=production rails assets:precompile

# Configure Nginx
sudo bash -c 'cat > /etc/nginx/conf.d/frozen-desserts.conf <<EOF
server {
    listen 80;
    server_name _;

    root /var/www/frozen-desserts/public;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    error_page 500 502 503 504 /500.html;
    client_max_body_size 4G;
    keepalive_timeout 10;
}
EOF'

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Start the Rails server
sudo bash -c 'RAILS_ENV=production bundle exec rails server -b 0.0.0.0 -p 3000 &'
'''

# Create an EC2 instance
server = ec2.Instance('web-server-www',
    instance_type='t2.micro',
    security_groups=[security_group.name],
    ami=ami.id,
    user_data=user_data,
    tags={"Name": "frozen-desserts-server"})

# Export the public IP and DNS of the instance
pulumi.export('publicIp', server.public_ip)
pulumi.export('publicHostName', server.public_dns)
