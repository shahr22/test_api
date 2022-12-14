from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_logs as logs,
    aws_iam as _iam,
    aws_lambda as _lambda,
    CfnOutput,
    Duration
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

        msal_layer = _lambda.LayerVersion(self, "MSALLayer",
            code=_lambda.Code.from_asset('lambda/layers/msal_requests'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            )
        
        route = api.root.add_resource('in')

        CfnOutput(self, "api-export", export_name="test-api-id", value=api.rest_api_id)

        CfnOutput(self, "api-resource-export", export_name= "test-path", value=route.resource_id)

        CfnOutput(self, "msal-layer", export_name= "msal-layer", value=msal_layer.layer_version_arn)

        interview_reminder = Route(self, "InterviewReminder",
            name='InterviewReminder',
            api=api,
            lambda_data={
                'code': _lambda.Code.from_asset('lambda/interview_reminder'),
                'layers': [msal_layer],
                'managed_policies': ["SecretsManagerReadWrite"]
            },
            api_config={
                'method' : "POST",
                'require_key': True
            },
            timeout=Duration.minutes(15)
        )

        deployment = apigw.Deployment(
            self,
            id="Deployment",
            api=api
        )