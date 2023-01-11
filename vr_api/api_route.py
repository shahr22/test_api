from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
  aws_iam as _iam,  
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct
import json

class Route(Construct):
    def __init__(self, scope: Construct, id: str, name, api, lambda_data, api_config, timeout, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        lambda_role = _iam.Role(scope=self, id=name+'LambdaRole',
            assumed_by =_iam.ServicePrincipal('lambda.amazonaws.com'),
            role_name=name+'LambdaRole',
            managed_policies=[
            _iam.ManagedPolicy.from_aws_managed_policy_name(
                'service-role/AWSLambdaBasicExecutionRole')  
            ]
        )
        
        if 'managed_policies' in lambda_data:
            for policy in lambda_data['managed_policies']:
                lambda_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name(policy))

        if 'policy_statements' in lambda_data:
            for policy in lambda_data['policy_statements']:
                lambda_role.add_to_policy(policy)

        route_lambda = _lambda.Function(
                self, name+'Lambda',
                runtime=_lambda.Runtime.PYTHON_3_9,
                code=lambda_data['code'],
                handler='main.handler',
                role=lambda_role,
                layers=lambda_data['layers'],
                timeout=timeout
            )

        route_lambda.add_permission('APIinvoke', principal=_iam.ServicePrincipal("apigateway.amazonaws.com"))

        route = api.root.add_resource(name+'route')

        route.add_method(api_config['method'], 
            apigw.LambdaIntegration(route_lambda),
            api_key_required=api_config['require_key'],
            )