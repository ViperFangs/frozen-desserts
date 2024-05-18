import pulumi
import pulumi_aws as aws
import base64

config = pulumi.Config()
db_username = config.require_secret("dbUsername")
db_password = config.require_secret("dbPassword")
rds_instance_id = config.require("rdsInstanceId")

# Read the deploy script
with open('deploy.sh', 'r') as deploy_file:
    deploy_script = deploy_file.read()

# Create a security group
security_group = aws.ec2.SecurityGroup('frozen-desserts-sg',
    description='Allow HTTP and SSH traffic',
    ingress=[
        {
            'protocol': 'tcp',
            'from_port': 22,
            'to_port': 22,
            'cidr_blocks': ['0.0.0.0/0'],
        },
        {
            'protocol': 'tcp',
            'from_port': 80,
            'to_port': 80,
            'cidr_blocks': ['0.0.0.0/0'],
        },
        {
            'protocol': 'tcp',
            'from_port': 443,
            'to_port': 443,
            'cidr_blocks': ['0.0.0.0/0'],
        },
    ],
    egress=[
        {
            'protocol': '-1',
            'from_port': 0,
            'to_port': 0,
            'cidr_blocks': ['0.0.0.0/0'],
        },
    ]
)

# Create an S3 bucket
bucket = aws.s3.Bucket('frozen-desserts-bucket')

# Reference an existing RDS instance
rds_instance = aws.rds.Instance.get("frozen-desserts-db", rds_instance_id)

deploy = pulumi.Output.all(db_username, db_password, rds_instance.address).apply(
    lambda args: deploy_script
                  .replace("${DB_USERNAME}", args[0])
                  .replace("${DB_PASSWORD}", args[1])
                  .replace("${DB_HOST}", args[2])
)

# Get the latest Amazon Linux 2 AMI
ami = aws.ec2.get_ami(most_recent=True, 
                      owners=["amazon"],
                      filters=[{"name": "name", "values": ["amzn2-ami-hvm-*"]}])

# Create an EC2 instance
instance = aws.ec2.Instance('frozen-desserts-instance',
                            instance_type='t2.micro',
                            ami=ami.id,
                            security_groups=[security_group.name],
                            user_data=deploy.apply(lambda script: base64.b64encode(script.encode('utf-8')).decode('utf-8')),
                            tags={"Name": "frozen-desserts-server"})

# Create an Elastic IP
elastic_ip = aws.ec2.Eip('frozen-desserts-eip', 
                         opts=pulumi.ResourceOptions(ignore_changes=["instance"]))

# Associate the Elastic IP with the EC2 instance
eip_association = aws.ec2.EipAssociation('frozen-desserts-eip-association',
                                         instance_id=instance.id,
                                         allocation_id=elastic_ip.id)

# Export the name of the bucket
pulumi.export('bucket_name', bucket.id)

# Export the Elastic IP
pulumi.export('elastic_ip', elastic_ip.public_ip)

# Export the Elastic IP
pulumi.export('rds_endpoint', rds_instance.endpoint)
