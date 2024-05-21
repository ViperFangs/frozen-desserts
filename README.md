# frozen-desserts

This project is an example on how to deploy a small Rails application on Amazon Web Services(AWS) using GitHub Actions and Pulumi. The project meets the following acceptance criteria:

### Completed Acceptance Criteria

1. **Fork the Repo**  
   The repository was forked from [https://github.com/strongmind/frozen-desserts](https://github.com/strongmind/frozen-desserts).
2. **Automatic Deployment using Github Actions and Pulumi**  
   The application deploys automatically to Amazon Web Services(AWS) from GitHub using GitHub Actions every time the main branch is updated.
3. **Fail Deployment on Test Failure**  
   The application runs the specs and fails to deploy if the specs fail.
4. **Available via HTTP**  
   The application is accessible from the internet via HTTP.
5. **Recreate AWS Resources**  
   The application uses Pulumi to generate and destroy AWS resources. Pulumi can also recreate instances if needed.
6. **Persist Data in Database**  
   Data is persisted in a Relation Database Service(RDS on AWS) PostgreSQL database.

### Future Improvements

- **Enable HTTPS**  
   Currently, the application is only accessible via HTTP. Enabling HTTPS would increase security.
- **Use Amazon Machine Image (AMI) for Faster Boot Times**  
   Creating a custom AMI with pre-installed dependencies such as ruby and rails can significantly reduce boot times.

### Deploy the Application

Push your changes to the `main` branch to trigger the GitHub Actions workflow that will deploy the application on AWS using Pulumi.

### Accessing the Application

Once deployed, the application will be accessible via the public IP of the Elastic IP assigned by AWS. The IP address will be outputted by Pulumi and can be found in the Pulumi stack outputs. This process can take up to 5 minutes.

# Original README Instructions

## Instructions

Deploy this small rails app, using AWS (You can use the free tier to test this)

## Acceptance Criteria

Acceptance criteria are listed in descending order of importance. Things closer to the bottom should be considered “stretch goals”. For example, you could deploy a version of this that uses sqlite and loses data when it is redeployed until you are able to persist data in a database.

1. it should fork the repo at https://github.com/strongmind/frozen-desserts
1. it should deploy automatically from github using github actions every time the main branch is updated
1. it should run the specs and fail to deploy if the specs fail
1. it should be available from the internet via http or https
1. it should recreate AWS resources if they are destroyed
1. it should persist data in a database
