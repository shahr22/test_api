from constructs import Construct
from aws_cdk import (
    Stack,
    pipelines as pipelines,
)
from vr_api.pipeline_stage import PipelineStage
from vr_api.pipeline_routes_stage import RouteStage
from os import getenv

# Pass code star connection as env variable
github_conn_arn=getenv('github_conn') 

class PipelineStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Uses CDK Pipelines instead of aws-codepipeline
        
        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            synth=pipelines.ShellStep(
                "Synth",                                           
                input=pipelines.CodePipelineSource.connection("shahr22/test_api", "master",
                    connection_arn=github_conn_arn
                ),
                commands=[
                    "npm install -g aws-cdk",                               
                    "pip install -r requirements.txt",
                    "pip install -r requirements_msal_layer.txt -t lambda/layers/msal_requests/python/lib/python3.9/site-packages", # for msal lambda layer                    
                    "cdk synth",                                      
                    ],
                primary_output_directory="cdk.out",
            ),
        )

        deploy = PipelineStage(self, "Deploy")
        deploy_stage = pipeline.add_stage(deploy)
        deploy_route = RouteStage(self, "DeployRoute")
        deploy_route_stage = pipeline.add_stage(deploy_route)

        