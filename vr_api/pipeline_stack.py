from constructs import Construct
from aws_cdk import (
    Stack,
    aws_codecommit as codecommit,
    pipelines as pipelines,
)
from vr_api.pipeline_stage import PipelineStage

GITHUB_ARN="arn:aws:codestar-connections:us-east-1:899456967600:connection/379f90c5-af81-46c2-b992-7c656c13c73c"

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
                    connection_arn=GITHUB_ARN
                ),
                commands=[
                    "npm install -g aws-cdk",                               
                    "pip install -r requirements.txt",
                    "pip install -r requirements_msal.txt -t lambda/layers/msal_requests/python/lib/python3.9/site-packages",                          
                    "cdk synth",                                      
                    ],
                primary_output_directory="cdk.out",
            ),
        )

        deploy = PipelineStage(self, "Deploy")
        deploy_stage = pipeline.add_stage(deploy)
        