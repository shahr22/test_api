from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_logs as logs,
    aws_iam as _iam,
    aws_lambda as _lambda
)

from constructs import Construct
from .api_route import Route

class VrApiStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        log_group = logs.LogGroup(self, "ApiGatewayAccessLogs")

        api = apigw.RestApi(self, "TestVrApi",
            deploy_options=apigw.StageOptions(
                access_log_destination=apigw.LogGroupLogDestination(log_group),
                access_log_format=apigw.AccessLogFormat.clf(),
            ),
            endpoint_configuration=apigw.EndpointConfiguration(
                types=[apigw.EndpointType.REGIONAL]
            )
        )

        api_key = api.add_api_key(
            id="ApiKey",
            api_key_name="pa-key"
        )

        plan = api.add_usage_plan("UsagePlan",
            name="Easy",
            throttle=apigw.ThrottleSettings(
                rate_limit=10,
                burst_limit=2
            )
        )

        plan.add_api_key(api_key)

        plan.add_api_stage(stage=api.deployment_stage)

        log_group = logs.LogGroup(self, "VrApiLogs")

        msal_layer = _lambda.LayerVersion(self, "MyLayer",
            code=_lambda.Code.from_asset('lambda/layers/msal_requests'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            )

        interview_reminder = Route(self, "InterviewReminder",
            name='InterviewReminder',
            api=api,
            lambda_data={
                'code': _lambda.Code.from_asset('lambda/interview_reminder'),
                'layers': [msal_layer],
                'managed_policies': "SecretsManagerReadWrite"
            },
            api_config={
                'method' : "POST",
                'require_key': True
            }

        )

        deployment = apigw.Deployment(
            self,
            id="Deployment",
            api=api
        )