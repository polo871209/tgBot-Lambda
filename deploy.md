# Step by Step how to deploy the code

I will skip through how to create an [AWS account](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/) and [telegram bot](https://flowxo.com/how-to-create-a-bot-for-telegram-short-and-simple-guide-for-beginners/), this won't take too much effort. Instead, this will focus on how you can deploy on AWS. Also, you should already have a sectigo account. If there is any naming require steps, I'll not specify. Leave anything default if not specify.

### Step 1. S3 Bucket
- Chose a region closest to your geo location. All the resource should be in this region to optimize speed.
- Create a S3 bucket. Leave every thing as default and name anything you like. In my case **'ssl-bucket'**(globally unique).
- Set lifcycle policy depends on your need, in my case 14 days to Glacier Instant Retrieval, delete after 400 days. [How to create lifcycle policy](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html) This will reduce the storage cost also cleaning bucket automatically.
---
![](https://i.imgur.com/77uC6O9.png)

### Step 2. IAM roles
to allow lambda to communicate with S3 you first need a role to grant permission to lambda.
- Create policy, go to IAM > policy > create policy JSON, below is the policy template, <your-bucket-name> as your bucket name, this will grant Lambda full access to your bucket.
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "s3-object-lambda:*"
            ],
            "Resource": [
                "arn:aws:s3:::<your-bucket-name>/*",
                "arn:aws:s3:::<your-bucket-name>"
            ]
        }
    ]
}
```
- Create role, go to role > create role > AWS service > lambda > permission policies chose policy you creat previously step. 

### Step 3. Lambda function
    
- runtime choose python3.7 if available, excucation rule chose what you set up last step. To grant perrmission to S3 bucket.
- upload [lambda_function.py](https://github.com/polo871209/tgBot-Lambda/blob/main/lambda_function.py), [aws.py](https://github.com/polo871209/tgBot-Lambda/blob/main/aws.py), [sectigo.py](https://github.com/polo871209/tgBot-Lambda/blob/main/sectigo.py), [tgbot.py](https://github.com/polo871209/tgBot-Lambda/blob/main/tgbot.py), than deploy
![](https://i.imgur.com/SG4y1kR.png)
- edit enviromant variable, configuration> enviromant variable
```
key                    value
api_token              <bot-api-token>
loginName              <sectigo-login-name>
loginPassword          <sectigo-login-password>
```
- Add lambda layer, modules ['requests'](https://pypi.org/project/requests/), ['pyopenssl'](https://pypi.org/project/pyOpenSSL/) are not included in the python lib, [here](https://www.linkedin.com/pulse/add-external-python-libraries-aws-lambda-using-layers-gabe-olokun/) is how you can update your external modules, update this two modules to lambda layers.
![](https://i.imgur.com/vM29DXy.png)
- Edit timeout, default lambda timeout is 3 seconds, however this would take about 17 seconds(inculd sectigo api response). So I set 20 second on timeout. configuration > general configuration > edit timeout.
    
### Step 4. API gateway
now is time to deploy your lambda function as rest API
- create api > rest api 
- action > create resource 
- under resource > create method ANY > 'Use Lambda Proxy integration'(important) > chose your lambda function.
- click on action > deploy api, than you should end up with an api url
![](https://i.imgur.com/RNLyD2R.png)

### Step 5. tgbot Webhook
Set Webhook:
https://api.telegram.org/bot<bot-api-token>/setWebhook?url=<api-gateway-url>  
**Than you are good to go.**  
here are some other webhook api I found useful:  
Remove Webhook:
https://api.telegram.org/bot<bot-api-token>/setWebhook?remove  
GetUpdate: (message recieve from webhook)  
https://api.telegram.org/bot<bot-api-token>/getUpdates  
offsetupdate: (offest incase message stuck  )
https://api.telegram.org/bot<bot-api-token>/getupdates?offset=<update-id>  
    