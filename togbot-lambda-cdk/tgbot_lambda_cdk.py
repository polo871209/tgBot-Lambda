from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_apigateway as apigateway
)

API_TOKEN = ""
LOGIN_NAME = ""
LOGIN_PASSWORD = ""
RUNE_TIME = lambda_.Runtime.PYTHON_3_7


class AwsCdkWorkshopStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # iam role
        lambda_role = iam.Role(
            self, "cdk-lambda-role-po",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="cdk-lambda-role-po"
        )
        # bucket
        bucket = s3.Bucket(
            self,
            "cdk-bucket-po",
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True
            )
        )
        bucket.grant_read_write(lambda_role)
        # lambda layer
        layer = lambda_.LayerVersion(
            self, "cdk-lambda-po-layer",
            code=lambda_.Code.from_asset('lambda_layer.zip'),
            compatible_runtimes=[RUNE_TIME],
            description="cdk-lambda-po-layer"
        )
        # lambda
        handler = lambda_.Function(
            self, "cdk-lambda-po",
            runtime=RUNE_TIME,
            handler="lambda_function.lambda_handler",
            code=lambda_.Code.from_asset('lambda_code.zip'),
            timeout=Duration.seconds(30),
            environment={
                "api_token": API_TOKEN,
                "loginName": "LOGIN_NAME",
                "loginPassword": LOGIN_PASSWORD
            },
            role=lambda_role
            # layers=[
            #     lambda_.ILayerVersion(
            #         compatible_runtimes=[RUNE_TIME]
            #     )
            # ]
        )
        # api gateway
        api = apigateway.RestApi(self, "cdk-api-po")
        v1 = api.root.add_resource("v1")
        ssl_bot = v1.add_resource("sslbot")
        integration = apigateway.LambdaIntegration(handler)
        ssl_bot.add_method("ANY", integration)
