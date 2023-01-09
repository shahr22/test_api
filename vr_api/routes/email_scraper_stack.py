from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    Fn,
    Duration
)

from constructs import Construct
from vr_api.api_route import Route


class EmailScraper(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api = apigw.RestApi.from_rest_api_attributes(
            self, "test-api",
            rest_api_id=Fn.import_value("test-api-id"),
            root_resource_id=Fn.import_value("test-path")
        )

        msal_layer = _lambda.LayerVersion.from_layer_version_arn(self, "msal-layer",Fn.import_value("msal-layer"))

        email_scraper = Route(self, "EmailScraper",
            name='EmailScraper',
            api=api,
            lambda_data={
                'code': _lambda.Code.from_asset('lambda/email_scraper'),
                'layers': [msal_layer],
                'managed_policies': ["SecretsManagerReadWrite"]
            },
            api_config={
                'method' : "POST",
                'require_key': True
            },
            timeout=Duration.minutes(15)
        )
