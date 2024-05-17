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
set -e

# Update and install necessary packages
sudo yum update -y
sudo amazon-linux-extras install nginx1 -y
sudo yum install -y git gcc make curl gpg

# Install RVM and Ruby 3.2.1
gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3 7D2BAF1CF37B13E2069D6956105BD0E739499BDB
curl -sSL https://get.rvm.io | bash -s stable
source /etc/profile.d/rvm.sh
rvm install 3.2.1
rvm use 3.2.1 --default

# Install Bundler and Rails
gem install bundler
gem install rails -v 7.0.8.1

# Clone the application repository
sudo git clone https://github.com/viperfangs/frozen-desserts.git /var/www/frozen-desserts

# Set up the application
cd /var/www/frozen-desserts
bundle install
yarn install

# Precompile assets
RAILS_ENV=production bundle exec rails assets:precompile

# Set up the database
RAILS_ENV=production bundle exec rails db:create
RAILS_ENV=production bundle exec rails db:migrate

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

# Start the Rails server with logging
bash -c 'cd /var/www/frozen-desserts && RAILS_ENV=production bundle exec rails server -b 0.0.0.0 -p 3000 > /var/log/rails.log 2>&1 &'
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
