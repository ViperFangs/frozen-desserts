import pulumi
import pulumi_aws as aws

# Read the user_data script
with open('user_data.sh', 'r') as user_data_file:
    user_data_script = user_data_file.read()

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
        {
            'protocol': 'tcp',
            'from_port': 3000,
            'to_port': 3000,
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

# Get the latest Amazon Linux 2 AMI
ami = aws.ec2.get_ami(most_recent=True,
                      owners=["amazon"],
                      filters=[{"name": "name", "values": ["amzn2-ami-hvm-*"]}])

# Create an EC2 instance
instance = aws.ec2.Instance('frozen-desserts-instance',
                            instance_type='t2.micro',
                            ami=ami.id,
                            security_groups=[security_group.name],
                            user_data=user_data_script,
                            tags={"Name": "frozen-desserts-server"})

# Export the name of the bucket
pulumi.export('bucket_name', bucket.id)

# Export the instance's public IP
pulumi.export('public_ip', instance.public_ip)
