#!/usr/bin/env python3

import aws_cdk as cdk

from aws_cdk_workshop.aws_cdk_workshop_stack import AwsCdkWorkshopStack


app = cdk.App()
AwsCdkWorkshopStack(app, "aws-cdk-workshop")

app.synth()
