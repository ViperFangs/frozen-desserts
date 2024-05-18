#!/bin/bash
# Update packages
sudo yum update -y

# Install dependencies
sudo yum install -y curl gpg gcc gcc-c++ make git gnupg2

# Remove old versions of PostgreSQL
sudo yum remove -y postgresql*

# Add the PostgreSQL 12 repository
sudo amazon-linux-extras enable postgresql12
sudo yum clean metadata
sudo yum install -y postgresql postgresql-devel

# Import the required GPG keys
curl -sSL https://rvm.io/mpapis.asc | gpg2 --import -
curl -sSL https://rvm.io/pkuczynski.asc | gpg2 --import -

# Install RVM
curl -sSL https://get.rvm.io | bash -s stable

# Load RVM
source /etc/profile.d/rvm.sh

# Install Ruby
rvm install 3.2.1
rvm use 3.2.1 --default

# Ensure home directory is set
export HOME=/home/ec2-user
cd $HOME

# Clone the repository
git clone https://github.com/viperfangs/frozen-desserts.git /home/ec2-user/frozen-desserts
cd /home/ec2-user/frozen-desserts

# Install Bundler Gem
gem install bundler

# Set environment variables for database (these will be replaced by Pulumi)
export DB_USERNAME="${DB_USERNAME}"
export DB_PASSWORD="${DB_PASSWORD}"
export DB_HOST="${DB_HOST}"

# Set up the Rails app
bundle install
rails db:create
rails db:migrate
rails server -b 0.0.0.0 -p 80 &