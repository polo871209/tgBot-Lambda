
# CDK Python project for tgBbot-lambda

**These cdk will deploy all the resources needed in the [tgBot-Lambda](https://github.com/polo871209/tgBot-Lambda) project**

You should explore the contents of this project. It demonstrates a CDK app with an instance of a stack (`togbot-lambda-cdk`)

## Setup
Set your credential using aws cli
```
$ aws configure
```

To manually create a virtualenv on macOS and Linux:

```
$ python -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

Now deploy all you resources!!

```
$ cdk deploy
```

Delete all the resources (except S3)

```
$ cdk destroy
```

Enjoy!