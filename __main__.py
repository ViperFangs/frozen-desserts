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

# Log output to file for troubleshooting
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# Update and install necessary packages
yum update -y
amazon-linux-extras install nginx1 -y
yum install -y git gcc make curl gpg

# Install RVM and Ruby 3.2.1
gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3 7D2BAF1CF37B13E2069D6956105BD0E739499BDB
curl -sSL https://get.rvm.io | bash -s stable
source /etc/profile.d/rvm.sh
rvm install 3.2.1
rvm use 3.2.1 --default

# Add the following to the .bashrc of the root and ec2-user to ensure RVM is loaded
echo "source /etc/profile.d/rvm.sh" >> /root/.bashrc
echo "source /etc/profile.d/rvm.sh" >> /home/ec2-user/.bashrc

# Make sure the changes are applied for the current session
source /root/.bashrc
source /home/ec2-user/.bashrc

# Install Bundler and Rails
gem install bundler
gem install rails -v 7.0.8.1

# Clone the application repository
git clone https://github.com/viperfangs/frozen-desserts.git /var/www/frozen-desserts

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
cat > /etc/nginx/conf.d/frozen-desserts.conf <<EOF
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
EOF

# Verify Nginx configuration file
if [ -f /etc/nginx/conf.d/frozen-desserts.conf ]; then
    echo "Nginx configuration file created successfully:"
    cat /etc/nginx/conf.d/frozen-desserts.conf
else
    echo "Failed to create Nginx configuration file."
    exit 1
fi

# Test Nginx configuration
nginx -t

# Start Nginx
systemctl enable nginx
systemctl start nginx

# Ensure Nginx is active
if systemctl is-active --quiet nginx; then
    echo "Nginx started successfully."
else
    echo "Nginx failed to start. Check logs for details."
    exit 1
fi

# Start the Rails server with logging
cd /var/www/frozen-desserts
RAILS_ENV=production bundle exec rails server -b 0.0.0.0 -p 3000 > /var/log/rails.log 2>&1 &

# Ensure Rails server is running
sleep 5
if pgrep -f "rails server" > /dev/null; then
    echo "Rails server started successfully."
else
    echo "Rails server failed to start. Check logs for details."
    exit 1
fi
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
