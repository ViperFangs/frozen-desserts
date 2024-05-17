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

# User data script to set up the server
user_data = '''#!/bin/bash
sudo yum update -y
sudo yum install -y ruby git httpd epel-release
sudo curl --fail -sSL https://rpm.nodesource.com/setup_14.x | sudo bash -
sudo curl --fail -sSL https://oss-binaries.phusionpassenger.com/yum/defs/el7/x86_64/passenger-release.repo -o /etc/yum.repos.d/passenger.repo
sudo yum install -y nginx passenger
sudo yum install -y mod_passenger

# Create Apache configuration for the Rails application
cat <<EOL | sudo tee /etc/httpd/conf.d/frozen-desserts.conf
LoadModule passenger_module /usr/lib/ruby/gems/2.7.0/gems/passenger-6.0.10/buildout/apache2/mod_passenger.so
<IfModule mod_passenger.c>
  PassengerRoot /usr/lib/ruby/gems/2.7.0/gems/passenger-6.0.10
  PassengerDefaultRuby /usr/bin/ruby
</IfModule>

<VirtualHost *:80>
  DocumentRoot /var/www/frozen-desserts/public

  <Directory /var/www/frozen-desserts/public>
    AllowOverride all
    Require all granted
    Options -MultiViews
  </Directory>
</VirtualHost>
EOL

# Clone the application repository
sudo git clone https://github.com/viperfangs/frozen-desserts.git /var/www/frozen-desserts

# Install Ruby gems
cd /var/www/frozen-desserts
sudo gem install bundler
sudo bundle install

# Set up the database
sudo RAILS_ENV=production rails db:create
sudo RAILS_ENV=production rails db:migrate

# Precompile assets
sudo RAILS_ENV=production rails assets:precompile

# Restart Apache
sudo systemctl restart httpd
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
